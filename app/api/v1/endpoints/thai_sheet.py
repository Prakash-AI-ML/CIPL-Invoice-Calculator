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

@router.post("/generate/docx1")
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
