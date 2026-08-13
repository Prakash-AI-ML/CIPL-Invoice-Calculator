
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

import uuid
from typing import List
import io
import pandas as pd
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, UploadFile, Request, HTTPException, Header
from typing import List, Optional
import json
import logging
from datetime import datetime
from app.cipl.extract import analysis_cipl, get_data_to_cipl
from app.cipl.documents import create_documents
from app.db.session import get_db
from app.api.dependencies import get_user_permissions_detailed
from app.crud.log_manage import backend_logs
import os
import io, uuid, zipfile, logging
from docx2pdf import convert
import platform
from app.cipl.pdf_extract import analysis_pdf_cipl, create_cipl_data
import pdfplumber
from app.crud.cipl_desc import get_cipl_descs
import tempfile
import subprocess
import shutil
from pathlib import Path

# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter() 

os_name = platform.system()

def convert_docx_to_pdf1(docx_path: str, output_dir: str):
    subprocess.run([
        "/usr/bin/libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        docx_path,
        "--outdir",
        output_dir
    ], check=True)

    pdf_path = Path(output_dir) / (Path(docx_path).stem + ".pdf")
    return str(pdf_path)

def convert_docs_pdf1(docx_temp_path, pdf_temp_path):
    if os_name == "Windows":
        print("Running on Windows")
        convert(docx_temp_path, pdf_temp_path)
    elif os_name == "Linux":
        print("Running on Linux")
        convert_docx_to_pdf(docx_temp_path, pdf_temp_path)



def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> str:
    """
    Convert a DOCX file to PDF using LibreOffice.

    docx_path:
        Full path to input .docx

    pdf_path:
        Full path where the resulting PDF should be placed.
        Example:
            /tmp/thai_pdf_xxx/output.pdf
    """

    docx_path = Path(docx_path).resolve()
    pdf_path = Path(pdf_path).resolve()

    if not docx_path.exists():
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")

    # LibreOffice --outdir requires a DIRECTORY,
    # not the final PDF filename.
    output_dir = pdf_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Give LibreOffice an isolated profile.
    # This avoids profile/lock problems when multiple FastAPI
    # requests perform conversions at the same time.
    lo_profile_dir = Path(
        tempfile.mkdtemp(prefix="libreoffice_profile_")
    ).resolve()

    try:
        result = subprocess.run(
            [
                "/usr/bin/libreoffice",
                "--headless",
                f"-env:UserInstallation=file://{lo_profile_dir}",
                "--convert-to",
                "pdf:writer_pdf_Export",
                "--outdir",
                str(output_dir),
                str(docx_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "LibreOffice PDF conversion failed.\n"
                f"Return code: {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        # LibreOffice creates:
        #
        # input.docx -> input.pdf
        #
        # regardless of the name we want for the final PDF.
        generated_pdf = output_dir / f"{docx_path.stem}.pdf"

        if not generated_pdf.exists():
            raise RuntimeError(
                "LibreOffice completed but the PDF was not created.\n"
                f"Expected: {generated_pdf}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        # Rename input.pdf -> requested output.pdf
        if generated_pdf != pdf_path:
            if pdf_path.exists():
                pdf_path.unlink()

            generated_pdf.rename(pdf_path)

        return str(pdf_path)

    finally:
        # Remove temporary LibreOffice profile
        shutil.rmtree(lo_profile_dir, ignore_errors=True)


def convert_docs_pdf(docx_temp_path: str, pdf_temp_path: str) -> str:
    """
    Cross-platform DOCX -> PDF wrapper.
    """

    if os.name == "nt":
        print("Running on Windows")
        return convert(docx_temp_path, pdf_temp_path)
    elif os.name == "posix":
        print("Running on Linux/Unix")
        return convert_docx_to_pdf(
                docx_path=docx_temp_path,
                pdf_path=pdf_temp_path,
            )
    else:
        raise RuntimeError(f"Unsupported operating system: {os.name}")

    


@router.post("/docx")
async def generate_docx_and_pdf(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    form = await request.form()
    mapping_data = await get_cipl_descs(db)

    DESCRIPTIONS_DATA = {
        "item_id": [],
        "original": [],
        "modified": [],
        "lines": []
    }

    for row in mapping_data:
        DESCRIPTIONS_DATA["item_id"].append(row.item_id)
        DESCRIPTIONS_DATA["original"].append(row.original)
        DESCRIPTIONS_DATA["modified"].append(row.modified)
        DESCRIPTIONS_DATA["lines"].append(row.lines)

    if not form:
        raise HTTPException(status_code=400, detail="No file uploaded")

    zip_buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            result_data = {}
            # Process each uploaded file
            for field_name, file in form.items():
                file_bytes = await file.read()
                original_filename = file.filename or f"input_{uuid.uuid4().hex[:8]}"

                if not original_filename.lower().endswith(('.xlsx', '.xls')):
                    raise HTTPException(status_code=415, detail=f"Unsupported file type: {original_filename}")

                file_io = io.BytesIO(file_bytes)

                # Read Excel sheets
                if original_filename.lower().endswith('.xlsx'):
                    df = pd.read_excel(file_io, engine='openpyxl', sheet_name=0)
                    df1 = pd.read_excel(file_io, engine='openpyxl', sheet_name=1)
                else:
                    df = pd.read_excel(file_io, engine='xlrd', sheet_name=0)
                    df1 = pd.read_excel(file_io, engine='xlrd', sheet_name=1)

                if df.empty or df1.empty:
                    raise HTTPException(status_code=400, detail="Empty sheet(s) in Excel file")

                # Your analysis logic
                result = analysis_cipl(df, df1, divided_by=divided_by, DESCRIPTIONS_DATA = DESCRIPTIONS_DATA)
                

                

                # Prepare clean filenames
                base_name = original_filename.rsplit(".", 1)[0].replace(" ", "_").replace(".", "_")
                docx_filename = f"{base_name}.docx"
                pdf_filename  = f"{base_name}.pdf"
                result_data[base_name] = result
                # ─── Create DOCX in memory ───────────────────────────────────────
                document = create_documents(data=result, filename=docx_filename)

                docx_buffer = io.BytesIO()
                document.save(docx_buffer)
                docx_buffer.seek(0)

                # ─── Convert DOCX → PDF using docx2pdf + temp files ──────────────
                with tempfile.TemporaryDirectory(prefix="cipl_") as tmp_dir:
                    docx_temp_path = os.path.join(tmp_dir, "temp_input.docx")
                    pdf_temp_path  = os.path.join(tmp_dir, "temp_output.pdf")

                    # Write DOCX bytes to disk (docx2pdf requires file paths)
                    with open(docx_temp_path, "wb") as f:
                        f.write(docx_buffer.getvalue())

                    # Perform conversion (input_path → output_path)
                    convert_docs_pdf(docx_temp_path, pdf_temp_path)

                    # Read generated PDF back to memory
                    with open(pdf_temp_path, "rb") as f:
                        pdf_bytes = f.read()

                pdf_buffer = io.BytesIO(pdf_bytes)
                pdf_buffer.seek(0)
                docx_buffer.seek(0)  # reset if needed later

                
              
                # ─── Add DOCX and PDF files to the ZIP ──────────────────────────
                zipf.writestr(f"WORD/{docx_filename}", docx_buffer.getvalue())
                zipf.writestr(f"PDF/{pdf_filename}", pdf_buffer.getvalue())
            # Convert the result to JSON format
            result_json = json.dumps(result_data, ensure_ascii=False, indent=4)
            
            # Add the JSON content to the ZIP file
            zipf.writestr('results.json', result_json)

        zip_buffer.seek(0)
        

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="converted_files.zip"'
            }
        )

    except Exception as e:
        logging.error(f"Error processing files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")



@router.post("/pdf-docx")
async def generate_docx_and_pdf(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    form = await request.form()
    mapping_data = await get_cipl_descs(db)

    DESCRIPTIONS_DATA = {
        "item_id": [],
        "original": [],
        "modified": [],
        "lines": []
    }

    for row in mapping_data:
        DESCRIPTIONS_DATA["item_id"].append(row.item_id)
        DESCRIPTIONS_DATA["original"].append(row.original)
        DESCRIPTIONS_DATA["modified"].append(row.modified)
        DESCRIPTIONS_DATA["lines"].append(row.lines)

    if not form:
        raise HTTPException(status_code=400, detail="No file uploaded")

    zip_buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            result_data = {}
            results = {
                'commercial_invoice': {},
                "packing_list":{}
            }
            # Process each uploaded file
            for field_name, file in form.items():
                file_bytes = await file.read()
                original_filename = file.filename or f"input_{uuid.uuid4().hex[:8]}"

                if not original_filename.lower().endswith(('.pdf')):
                    raise HTTPException(status_code=415, detail=f"Unsupported file type: {original_filename}")

                file_io = io.BytesIO(file_bytes)

                # Read Excel sheets
                if original_filename.lower().endswith('.pdf'):
                    # Read PDF
                    with pdfplumber.open(file_io) as pdf:
                        page = pdf.pages[0]

                    data = analysis_pdf_cipl(page, divided_by = divided_by, DESCRIPTIONS_DATA = DESCRIPTIONS_DATA)
                    if data['invoice_type'] == 'COMMERCIAL INVOICE':
                        results['commercial_invoice'][data['reference_no']] = data
                    else:
                        results['packing_list'][data['reference_no']] = data

            cipl_data = create_cipl_data(results, DESCRIPTIONS_DATA = DESCRIPTIONS_DATA)


            for key, value in cipl_data.items():

                # Prepare clean filenames
                base_name = f"CIPL_{key}-{'FNL' if divided_by else 'ORI'}"
                docx_filename = f"{base_name}.docx"
                pdf_filename  = f"{base_name}.pdf"
                # ─── Create DOCX in memory ───────────────────────────────────────
                document = create_documents(data=value, filename=docx_filename)

                docx_buffer = io.BytesIO()
                document.save(docx_buffer)
                docx_buffer.seek(0)

                # ─── Convert DOCX → PDF using docx2pdf + temp files ──────────────
                with tempfile.TemporaryDirectory(prefix="cipl_") as tmp_dir:
                    docx_temp_path = os.path.join(tmp_dir, "temp_input.docx")
                    pdf_temp_path  = os.path.join(tmp_dir, "temp_output.pdf")

                    # Write DOCX bytes to disk (docx2pdf requires file paths)
                    with open(docx_temp_path, "wb") as f:
                        f.write(docx_buffer.getvalue())

                    # Perform conversion (input_path → output_path)
                    convert_docs_pdf(docx_temp_path, pdf_temp_path)

                    # Read generated PDF back to memory
                    with open(pdf_temp_path, "rb") as f:
                        pdf_bytes = f.read()

                pdf_buffer = io.BytesIO(pdf_bytes)
                pdf_buffer.seek(0)
                docx_buffer.seek(0)  # reset if needed later

                
              
                # ─── Add DOCX and PDF files to the ZIP ──────────────────────────
                zipf.writestr(f"WORD/{docx_filename}", docx_buffer.getvalue())
                zipf.writestr(f"PDF/{pdf_filename}", pdf_buffer.getvalue())
            # Convert the result to JSON format
            result_json = json.dumps(cipl_data, ensure_ascii=False, indent=4)
            
            # Add the JSON content to the ZIP file
            zipf.writestr('results.json', result_json)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="converted_files.zip"'
            }
        )

    except Exception as e:
        logging.error(f"Error processing files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")



@router.post("/pdf-preview")
async def generate_docx_and_pdf(
    request: Request,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    mapping_data = await get_cipl_descs(db)

    DESCRIPTIONS_DATA = {
        "item_id": [],
        "original": [],
        "modified": [],
        "lines": [],
    }

    for row in mapping_data:
        DESCRIPTIONS_DATA["item_id"].append(row.item_id)
        DESCRIPTIONS_DATA["original"].append(row.original)
        DESCRIPTIONS_DATA["modified"].append(row.modified)
        DESCRIPTIONS_DATA["lines"].append(row.lines)

    zip_buffer = io.BytesIO()

    try:
        with zipfile.ZipFile(
            zip_buffer,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zipf:

            result_data = {}

            for key, value in data.items():

                # ─── Prepare clean filenames ───────────────────────────────
                base_name = f"CIPL_{key}"
                docx_filename = f"{base_name}.docx"
                pdf_filename = f"{base_name}.pdf"

                # ─── Prepare CIPL data ─────────────────────────────────────
                value = get_data_to_cipl(
                    value,
                    DESCRIPTIONS_DATA
                )

                result_data[key] = value

                # ─── Create DOCX in memory ──────────────────────────────────
                document = create_documents(
                    data=value,
                    filename=docx_filename
                )

                docx_buffer = io.BytesIO()
                document.save(docx_buffer)
                docx_buffer.seek(0)

                # ─── Convert DOCX → PDF ────────────────────────────────────
                #
                # LibreOffice's --outdir expects a DIRECTORY.
                # It will create:
                #
                # pdf_output_dir/
                #     temp_input.pdf
                #
                with tempfile.TemporaryDirectory(
                    prefix="cipl_"
                ) as tmp_dir:

                    docx_temp_path = os.path.join(
                        tmp_dir,
                        "temp_input.docx"
                    )

                    pdf_output_dir = os.path.join(
                        tmp_dir,
                        "pdf_output"
                    )

                    os.makedirs(
                        pdf_output_dir,
                        exist_ok=True
                    )

                    # Write DOCX bytes to temporary file
                    with open(docx_temp_path, "wb") as f:
                        f.write(docx_buffer.getvalue())

                    # Convert DOCX → PDF
                    #
                    # IMPORTANT:
                    # pdf_output_dir is a DIRECTORY, not a .pdf file.
                    #
                    convert_docs_pdf(
                        docx_temp_path,
                        pdf_output_dir
                    )

                    # LibreOffice generates the PDF using
                    # the input filename:
                    #
                    # temp_input.docx → temp_input.pdf
                    #
                    pdf_temp_path = os.path.join(
                        pdf_output_dir,
                        "temp_input.pdf"
                    )

                    # Make sure conversion actually produced the PDF
                    if not os.path.isfile(pdf_temp_path):
                        # Include directory contents in the error to make
                        # future debugging easier.
                        generated_files = []

                        if os.path.exists(pdf_output_dir):
                            generated_files = os.listdir(
                                pdf_output_dir
                            )

                        raise FileNotFoundError(
                            "PDF conversion completed but the expected "
                            f"PDF was not found: {pdf_temp_path}. "
                            f"Generated files: {generated_files}"
                        )

                    # Read PDF into memory before TemporaryDirectory
                    # is automatically deleted
                    with open(pdf_temp_path, "rb") as f:
                        pdf_bytes = f.read()

                # ─── Prepare PDF buffer ─────────────────────────────────────
                pdf_buffer = io.BytesIO(pdf_bytes)
                pdf_buffer.seek(0)

                # Reset DOCX buffer
                docx_buffer.seek(0)

                # ─── Add DOCX and PDF to ZIP ────────────────────────────────
                zipf.writestr(
                    f"WORD/{docx_filename}",
                    docx_buffer.getvalue()
                )

                zipf.writestr(
                    f"PDF/{pdf_filename}",
                    pdf_buffer.getvalue()
                )

            # ─── Convert result data to JSON ────────────────────────────────
            result_json = json.dumps(
                result_data,
                ensure_ascii=False,
                indent=4
            )

            # ─── Add JSON to ZIP ────────────────────────────────────────────
            zipf.writestr(
                "results.json",
                result_json
            )

        # Reset ZIP buffer before sending response
        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": (
                    'attachment; filename="converted_files.zip"'
                )
            }
        )

    except Exception as e:
        logging.error(
            f"Error processing files: {str(e)}",
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

@router.post("/download-docx")
async def download_docx(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    form = await request.form()
    mapping_data = await get_cipl_descs(db)

    DESCRIPTIONS_DATA = {
        "item_id": [],
        "original": [],
        "modified": [],
        "lines": []
    }

    for row in mapping_data:
        DESCRIPTIONS_DATA["item_id"].append(row.item_id)
        DESCRIPTIONS_DATA["original"].append(row.original)
        DESCRIPTIONS_DATA["modified"].append(row.modified)
        DESCRIPTIONS_DATA["lines"].append(row.lines)

    if not form:
        raise HTTPException(status_code=400, detail="No file uploaded")

    
    try:
        
        result_data = {}
        results = {
            'commercial_invoice': {},
            "packing_list":{}
        }
        # Process each uploaded file
        for field_name, file in form.items():
            file_bytes = await file.read()
            original_filename = file.filename or f"input_{uuid.uuid4().hex[:8]}"

            if not original_filename.lower().endswith(('.pdf')):
                raise HTTPException(status_code=415, detail=f"Unsupported file type: {original_filename}")

            file_io = io.BytesIO(file_bytes)

            # Read Excel sheets
            if original_filename.lower().endswith('.pdf'):
                # Read PDF
                with pdfplumber.open(file_io) as pdf:
                    page = pdf.pages[0]

                data = analysis_pdf_cipl(page, divided_by = divided_by, DESCRIPTIONS_DATA = DESCRIPTIONS_DATA)
                if data['invoice_type'] == 'COMMERCIAL INVOICE':
                    results['commercial_invoice'][data['reference_no']] = data
                else:
                    results['packing_list'][data['reference_no']] = data

        cipl_data = create_cipl_data(results, DESCRIPTIONS_DATA = DESCRIPTIONS_DATA)


        for key, value in cipl_data.items():

            # Prepare clean filenames
            base_name = f"CIPL_{key}-{'FNL' if divided_by else 'ORI'}"
            docx_filename = f"{base_name}.docx"
            # ─── Create DOCX in memory ───────────────────────────────────────
            document = create_documents(data=value, filename=docx_filename)

            docx_buffer = io.BytesIO()
            document.save(docx_buffer)
            docx_buffer.seek(0)

            return StreamingResponse(
                                    docx_buffer,
                                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    headers={"Content-Disposition": f'attachment; filename="{base_name}.docx"'},
                                )

               
    except Exception as e:
        logging.error(f"Error processing files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


