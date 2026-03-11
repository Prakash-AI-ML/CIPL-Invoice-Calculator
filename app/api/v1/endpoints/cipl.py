
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
from app.cipl.extract import analysis_cipl
from app.cipl.documents import create_documents
from app.db.session import get_db
from app.api.dependencies import get_user_permissions_detailed
from app.crud.log_manage import backend_logs
import os
import io, uuid, zipfile, logging
from docx2pdf import convert

import tempfile


# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter() 




@router.post("/docx1")
async def generate_docx_and_pdf(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    form = await request.form()

    if not form:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Process the first file only (extend later if needed)
    field_name, file = next(iter(form.items()))

    try:
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
        result = analysis_cipl(df, df1, divided_by=divided_by)

        # Prepare clean filenames
        base_name = original_filename.rsplit(".", 1)[0].replace(" ", "_").replace(".", "_")
        docx_filename = f"{base_name}.docx"
        pdf_filename  = f"{base_name}.pdf"

        # ─── Create DOCX in memory ───────────────────────────────────────
        document = create_documents(data=result, filename=docx_filename)

        docx_buffer = io.BytesIO()
        document.save(docx_buffer)
        docx_buffer.seek(0)

        # ─── Convert DOCX → PDF using docx2pdf + temp files ──────────────
        with tempfile.TemporaryDirectory() as tmp_dir:
            docx_temp_path = os.path.join(tmp_dir, "temp_input.docx")
            pdf_temp_path  = os.path.join(tmp_dir, "temp_output.pdf")

            # Write DOCX bytes to disk (docx2pdf requires file paths)
            with open(docx_temp_path, "wb") as f:
                f.write(docx_buffer.getvalue())

            # Perform conversion (input_path → output_path)
            convert(docx_temp_path, pdf_temp_path)

            # Read generated PDF back to memory
            with open(pdf_temp_path, "rb") as f:
                pdf_bytes = f.read()

        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        docx_buffer.seek(0)  # reset if needed later

        # ─── Create ZIP with both files ──────────────────────────────────
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(docx_filename, docx_buffer.getvalue())
            zipf.writestr(pdf_filename, pdf_buffer.getvalue())

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{base_name}_report.zip"'
            }
        )

    except Exception as e:
        logging.error(f"Error processing file '{original_filename}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")



@router.post("/docx")
async def generate_docx_and_pdf(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    form = await request.form()

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
                result = analysis_cipl(df, df1, divided_by=divided_by)
                

                

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
                    convert(docx_temp_path, pdf_temp_path)

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

from app.cipl.pdf_extract import analysis_pdf_cipl, create_cipl_data
import pdfplumber

@router.post("/pdf-docx")
async def generate_docx_and_pdf(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    form = await request.form()

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

                    data = analysis_pdf_cipl(page, divided_by)
                    if data['invoice_type'] == 'COMMERCIAL INVOICE':
                        results['commercial_invoice'][data['reference_no']] = data
                    else:
                        results['packing_list'][data['reference_no']] = data

            cipl_data = create_cipl_data(results)


            for key, value in cipl_data.items():

                # Prepare clean filenames
                base_name = f'CIPL_{key}'
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
                    convert(docx_temp_path, pdf_temp_path)

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

