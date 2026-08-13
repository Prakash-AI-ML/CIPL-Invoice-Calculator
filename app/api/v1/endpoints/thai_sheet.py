from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List
import os
import tempfile
import shutil
from pathlib import Path
from docx import Document
import pandas as pd

from fastapi import HTTPException, Header
from app.thai.sheet import *
from app.api.dependencies import get_user_permissions_detailed
from app.crud.log_manage import backend_logs
from app.tally_sheet.tally_sheet import *
import io
from io import BytesIO
from app.thai.customs_docx import create_thai_document
import traceback
import tempfile
import io, uuid, zipfile, logging
from docx2pdf import convert
import subprocess
from pathlib import Path
import platform
# ─── FastAPI app ────────────────────────────────────────

router = APIRouter() 


os_name = platform.system()

def convert_docx_to_pdf(docx_path: str, output_dir: str):
    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        docx_path,
        "--outdir",
        output_dir
    ], check=True)

    pdf_path = Path(output_dir) / (Path(docx_path).stem + ".pdf")
    return str(pdf_path)

def convert_docs_pdf(docx_temp_path, pdf_temp_path):
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

    




@router.post("/generate/sheet")
async def generate_thai_sheet(
    data: dict
):
    # We'll keep the temp directory until AFTER we send the response
    # → use manual cleanup instead of with-statement
    tmp_dir = None
    try:
        tmp_dir = Path(tempfile.mkdtemp(prefix="thai_"))
        print(f"Created temp dir: {tmp_dir}")

        
        # ─── Process documents ────────────────────────────────
        original_data, final_data, file_range = create_thai_data(data = data)
        

        if not original_data or not final_data:
            raise HTTPException(400, "No valid data extracted from uploaded Word files")

        ori_df = pd.DataFrame(original_data)
        fnl_df = pd.DataFrame(final_data)
        print("ORIGINAL DataFrame shape:", ori_df.shape, "\n FINAL DataFrame shape:", fnl_df.shape)

        # Output file
        output_excel = os.path.join(tmp_dir, f"THAI_DOCUMENT_SHEET_{file_range}.xlsx" )

        # This is the critical part — catch & log any error
        try:
            create_thai_sheet(ori_df, fnl_df, output_excel)
        except Exception as exc:
            print("ERROR during create_tally_sheet:")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate Excel file: {str(exc)}"
            )

     
        # Send file — file will be kept open until response is sent
        return FileResponse(
            path=output_excel,
            filename=f"THAI_DOCUMENT_SHEET_{file_range}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        traceback.print_exc()

    except Exception as e:
        raise HTTPException(500, f"Server error: {str(e)}")

    # finally:
    #     # Clean up temp folder — runs even if exception occurred
    #     if tmp_dir is not None and tmp_dir.exists():
    #         try:
    #             shutil.rmtree(tmp_dir, ignore_errors=True)
    #             print(f"Cleaned up: {tmp_dir}")
    #         except Exception as cleanup_err:
    #             print(f"Cleanup failed: {cleanup_err}")



@router.post("/generate/docx")
async def generate_tally_sheet(
    verification: bool,
    fnl_to_ori: bool,
    draft_docx: UploadFile = File(...),
    thai_sheet: UploadFile = File(...)
):
    if not draft_docx or not thai_sheet:
        raise HTTPException(400, "Both draft_docx and thai_sheet are required")

    # We'll keep the temp directory until AFTER we send the response
    # → use manual cleanup instead of with-statement
    tmp_dir = None
    try:
        tmp_dir = Path(tempfile.mkdtemp(prefix="thai_"))
        print(f"Created temp dir: {tmp_dir}")

        

        # Save uploaded files
        
        if not draft_docx.filename.lower().endswith(('.docx', '.doc')):
            raise HTTPException(400, f"Only .docx files allowed. Got: {draft_docx.filename}")
        dest = tmp_dir / draft_docx.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(draft_docx.file, f)
        if not thai_sheet.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(400, f"Only '.xlsx' or '.xls' files allowed. Got: {thai_sheet.filename}")
        
        # ─── Process excel ────────────────────────────────
        if thai_sheet.filename.lower().endswith(('.xlsx', '.xls')):
            # file_io = io.BytesIO(await thai_sheet.file.read())
            file_io = io.BytesIO(await thai_sheet.read())

            if thai_sheet.filename.lower().endswith('.xlsx'):
                ori = pd.read_excel(file_io, sheet_name="ORIGINAL", engine='openpyxl')
                fnl = pd.read_excel(file_io, sheet_name="FINAL", engine='openpyxl')
            else:
                ori = pd.read_excel(file_io, sheet_name="ORIGINAL", engine='xlrd')
                fnl = pd.read_excel(file_io, sheet_name="FINAL", engine='xlrd')
        
        index_ = ori[ori['REF NO'].isnull()].index
        columns = ['AMOUNT', 'THB', '10%', 'THB+10%', '7%', 'PAGE TOTAL']
        for col in columns:
            ori[col] = ori[col].apply(
                lambda val: f"{val:,.2f}" if pd.notna(val) else val
            )
        for col in columns:
            fnl[col] = fnl[col].apply(
                lambda val: f"{val:,.2f}" if pd.notna(val) else val
            )
        fnl = fnl[columns]
        ori = ori[columns]

        # ─── Process documents ────────────────────────────────
        
        doc = await create_thai_document(ori, fnl, dest, index_, verification, fnl_to_ori)
        
  

        # Output file
        output_file_name = f"{draft_docx.filename.split('.docx')[0]}-{'ORI' if fnl_to_ori else 'FNL'}.docx"
        output_file = os.path.join(tmp_dir, f"{draft_docx.filename.split('.docx')[0]}-{'ORI' if verification else 'FNL'}")

        # This is the critical part — catch & log any error
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=f'{output_file_name}'"}
        )

    except Exception as e:
        error_detail = traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_detail)

@router.post("/generate/docx1/old")
async def generate_tally_sheet(
    verification: bool,
    fnl_to_ori: bool,
    draft_docx: UploadFile = File(...),
    thai_sheet: UploadFile = File(...)
):
    if not draft_docx or not thai_sheet:
        raise HTTPException(400, "Both draft_docx and thai_sheet are required")

    try:
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:

            # ─── Create temp dir ────────────────────────────────
            tmp_dir = Path(tempfile.mkdtemp(prefix="thai_"))

            # ─── Save DOCX template ─────────────────────────────
            if not draft_docx.filename.lower().endswith(('.docx', '.doc')):
                raise HTTPException(400, f"Only .docx files allowed. Got: {draft_docx.filename}")

            dest = tmp_dir / draft_docx.filename
            with dest.open("wb") as f:
                shutil.copyfileobj(draft_docx.file, f)

            # ─── Validate Excel ────────────────────────────────
            if not thai_sheet.filename.lower().endswith(('.xlsx', '.xls')):
                raise HTTPException(400, f"Only '.xlsx' or '.xls' files allowed. Got: {thai_sheet.filename}")

            file_io = io.BytesIO(await thai_sheet.read())

            # ─── Read Excel ────────────────────────────────────
            if thai_sheet.filename.lower().endswith('.xlsx'):
                ori = pd.read_excel(file_io, sheet_name="ORIGINAL", engine='openpyxl')
                fnl = pd.read_excel(file_io, sheet_name="FINAL", engine='openpyxl')
            else:
                ori = pd.read_excel(file_io, sheet_name="ORIGINAL", engine='xlrd')
                fnl = pd.read_excel(file_io, sheet_name="FINAL", engine='xlrd')

            # ─── Format Data ───────────────────────────────────
            index_ = ori[ori['REF NO'].isnull()].index
            columns = ['AMOUNT', 'THB', '10%', 'THB+10%', '7%', 'PAGE TOTAL']

            for col in columns:
                ori[col] = ori[col].apply(lambda val: f"{val:,.2f}" if pd.notna(val) else val)
                fnl[col] = fnl[col].apply(lambda val: f"{val:,.2f}" if pd.notna(val) else val)

            fnl = fnl[columns]
            ori = ori[columns]

            # ─── Generate DOCX ────────────────────────────────
            doc = await create_thai_document(ori, fnl, dest, index_, verification, fnl_to_ori)

            base_name = draft_docx.filename.rsplit(".", 1)[0]
            docx_filename = f"{base_name}-{'ORI' if fnl_to_ori else 'FNL'}{'-REVIEW' if verification else ''}.docx"
            pdf_filename = f"{base_name}-{'ORI' if fnl_to_ori else 'FNL'}{'-REVIEW' if verification else ''}.pdf"

            # ─── Save DOCX to memory ──────────────────────────
            docx_buffer = BytesIO()
            doc.save(docx_buffer)
            docx_buffer.seek(0)

            # ─── Convert DOCX → PDF ───────────────────────────
            with tempfile.TemporaryDirectory(prefix="thai_pdf_") as tmp:
                docx_path = os.path.join(tmp, "input.docx")
                pdf_path = os.path.join(tmp, "output.pdf")

                with open(docx_path, "wb") as f:
                    f.write(docx_buffer.getvalue())

                convert_docs_pdf(docx_path, pdf_path)

                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

            pdf_buffer = BytesIO(pdf_bytes)
            pdf_buffer.seek(0)
            docx_buffer.seek(0)

            # ─── Add to ZIP ───────────────────────────────────
            zipf.writestr(f"WORD/{docx_filename}", docx_buffer.getvalue())
            zipf.writestr(f"PDF/{pdf_filename}", pdf_buffer.getvalue())

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{base_name}_files.zip"'
            }
        )

    except Exception as e:
        error_detail = traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/generate/docx1")
async def generate_tally_sheet(
    verification: bool,
    fnl_to_ori: bool,
    draft_docx: UploadFile = File(...),
    thai_sheet: UploadFile = File(...),
):
    if not draft_docx or not thai_sheet:
        raise HTTPException(
            status_code=400,
            detail="Both draft_docx and thai_sheet are required",
        )

    tmp_dir = None

    try:
        # ====================================================
        # Create working temp directory
        # ====================================================

        tmp_dir = Path(
            tempfile.mkdtemp(prefix="thai_")
        ).resolve()

        # ====================================================
        # Validate DOCX
        # ====================================================

        if not draft_docx.filename:
            raise HTTPException(
                status_code=400,
                detail="draft_docx filename is missing",
            )

        if not draft_docx.filename.lower().endswith(".docx"):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Only .docx files are allowed. "
                    f"Got: {draft_docx.filename}"
                ),
            )

        # Use a fixed safe filename instead of trusting the uploaded
        # filename as a filesystem path.
        template_path = tmp_dir / "template.docx"

        with template_path.open("wb") as f:
            shutil.copyfileobj(draft_docx.file, f)

        # ====================================================
        # Validate Excel
        # ====================================================

        if not thai_sheet.filename:
            raise HTTPException(
                status_code=400,
                detail="thai_sheet filename is missing",
            )

        excel_filename = thai_sheet.filename.lower()

        if not excel_filename.endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Only .xlsx or .xls files are allowed. "
                    f"Got: {thai_sheet.filename}"
                ),
            )

        # Read uploaded Excel into memory
        excel_bytes = await thai_sheet.read()
        file_io = io.BytesIO(excel_bytes)

        # ====================================================
        # Read Excel
        # ====================================================

        if excel_filename.endswith(".xlsx"):
            ori = pd.read_excel(
                file_io,
                sheet_name="ORIGINAL",
                engine="openpyxl",
            )

            # Reset stream before reading second sheet
            file_io.seek(0)

            fnl = pd.read_excel(
                file_io,
                sheet_name="FINAL",
                engine="openpyxl",
            )

        else:
            ori = pd.read_excel(
                file_io,
                sheet_name="ORIGINAL",
                engine="xlrd",
            )

            file_io.seek(0)

            fnl = pd.read_excel(
                file_io,
                sheet_name="FINAL",
                engine="xlrd",
            )

        # ====================================================
        # Validate required columns
        # ====================================================

        required_columns = [
            "REF NO",
            "AMOUNT",
            "THB",
            "10%",
            "THB+10%",
            "7%",
            "PAGE TOTAL",
        ]

        missing_ori = [
            col for col in required_columns
            if col not in ori.columns
        ]

        missing_fnl = [
            col for col in required_columns
            if col not in fnl.columns
        ]

        if missing_ori:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Missing columns in ORIGINAL sheet: "
                    + ", ".join(missing_ori)
                ),
            )

        if missing_fnl:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Missing columns in FINAL sheet: "
                    + ", ".join(missing_fnl)
                ),
            )

        # ====================================================
        # Find index
        # ====================================================

        index_ = ori[ori["REF NO"].isnull()].index

        # ====================================================
        # Format numeric columns
        # ====================================================

        columns = [
            "AMOUNT",
            "THB",
            "10%",
            "THB+10%",
            "7%",
            "PAGE TOTAL",
        ]

        for col in columns:
            ori[col] = ori[col].apply(
                lambda val: (
                    f"{val:,.2f}"
                    if pd.notna(val)
                    else val
                )
            )

            fnl[col] = fnl[col].apply(
                lambda val: (
                    f"{val:,.2f}"
                    if pd.notna(val)
                    else val
                )
            )

        fnl = fnl[columns]
        ori = ori[columns]

        # ====================================================
        # Generate DOCX
        # ====================================================

        doc = await create_thai_document(
            ori,
            fnl,
            template_path,
            index_,
            verification,
            fnl_to_ori,
        )

        # ====================================================
        # Generate filenames
        # ====================================================

        original_base_name = Path(
            draft_docx.filename
        ).stem

        mode = "ORI" if fnl_to_ori else "FNL"
        review = "-REVIEW" if verification else ""

        docx_filename = (
            f"{original_base_name}-{mode}{review}.docx"
        )

        pdf_filename = (
            f"{original_base_name}-{mode}{review}.pdf"
        )

        zip_filename = (
            f"{original_base_name}_files.zip"
        )

        # ====================================================
        # Save generated DOCX
        # ====================================================

        generated_docx_path = tmp_dir / docx_filename

        doc.save(str(generated_docx_path))

        # ====================================================
        # Convert DOCX -> PDF
        # ====================================================

        generated_pdf_path = tmp_dir / pdf_filename

        convert_docs_pdf(
            str(generated_docx_path),
            str(generated_pdf_path),
        )

        # ====================================================
        # Verify PDF
        # ====================================================

        if not generated_pdf_path.exists():
            raise RuntimeError(
                f"PDF was not generated: {generated_pdf_path}"
            )

        # ====================================================
        # Create ZIP in memory
        # ====================================================

        zip_buffer = BytesIO()

        with zipfile.ZipFile(
            zip_buffer,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zipf:

            # Add DOCX
            with generated_docx_path.open("rb") as f:
                zipf.writestr(
                    f"WORD/{docx_filename}",
                    f.read(),
                )

            # Add PDF
            with generated_pdf_path.open("rb") as f:
                zipf.writestr(
                    f"PDF/{pdf_filename}",
                    f.read(),
                )

        zip_buffer.seek(0)

        # ====================================================
        # Return ZIP
        # ====================================================

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{zip_filename}"'
                )
            },
        )

    except HTTPException:
        # Don't turn intentional 400 errors into 500 errors
        raise

    except Exception as e:
        error_detail = traceback.format_exc()

        print(error_detail)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:
        # ====================================================
        # Cleanup working directory
        # ====================================================

        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(
                tmp_dir,
                ignore_errors=True,
            )
