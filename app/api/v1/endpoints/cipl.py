
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



# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter() 

@router.post("/docx1")
async def list_subscribers(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    # # # 🔐 Backend safety check (DO NOT rely only on frontend)
    # if not current_user.get("can_impersonate") and not current_user.get("impersonated"):
    #     raise HTTPException(status_code=403, detail="Permission denied")
    
    description = f"CIPL Document generator accessed by authenticated user: {current_user['username']} "
    action = 'CIPL Document generator'
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/cipl/docx',
                        action= action, description= description, is_backend= True, input_params= None)

    form = await request.form()
    output_results = []
    for field_name, file in form.items():
        
        try:
            file_bytes = await file.read()
            file_name = file.filename or f"{uuid.uuid4()}"

            if not file_name.lower().endswith(( '.xlsx',  '.xls')):
                raise HTTPException(status_code=415, detail=f"Unsupported file type: {file_name}")
            

            if  file_name.lower().endswith(('.xlsx', '.xls')):
                file_io = io.BytesIO(file_bytes)

                if file_name.lower().endswith('.xlsx'):
                    df = pd.read_excel(file_io, engine='openpyxl', sheet_name=0)
                    df1 = pd.read_excel(file_io, engine='openpyxl', sheet_name=1)
                else:
                    df = pd.read_excel(file_io, engine='xlrd', sheet_name=0)
                    df1 = pd.read_excel(file_io, engine='xlrd', sheet_name=1)

                if df.empty or df1.empty:
                    output_results.append({
                        "filename": file_name,
                        "responses": {"error": "Empty Excel file"}
                    })
                    continue
                file_name_ = f"{file_name.replace(' ', '_').split('.')[0]}.docx"
                result = analysis_cipl(df, df1, divided_by= divided_by)
                document = create_documents(data= result, filename= file_name_)

                # Save to memory buffer
                buffer = io.BytesIO()
                document.save(buffer)
                buffer.seek(0)

                # Return as response
                # return StreamingResponse(
                #     buffer,
                #     media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                #     # media_type="application/docx",
                #     headers={
                #         "Content-Disposition": f"attachment; filename={file_name_}"
                #     }
                # )
                # clean_result = jsonable_encoder(result)

                output_results.append({
                    "filename": file_name,
                    "responses": {"pdf": file1.getvalue().decode(), "docx": file2.getvalue().decode()}
                })

        except Exception as e:
            logging.error(f"Error processing file '{file_name}': {e}")
            raise HTTPException(status_code=500, detail=f"Error processing file '{file_name}': {e}")

    return JSONResponse(content=output_results)


import io, uuid, zipfile, logging
from docx2pdf import convert


@router.post("/docx2")
async def list_subscribers(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    form = await request.form()
    output_results = []

    # Prepare in-memory ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:

        for field_name, file in form.items():
            try:
                file_bytes = await file.read()
                file_name = file.filename or f"{uuid.uuid4()}"

                if not file_name.lower().endswith(('.xlsx', '.xls')):
                    raise HTTPException(status_code=415, detail=f"Unsupported file type: {file_name}")

                # Read Excel sheets
                file_io = io.BytesIO(file_bytes)
                if file_name.lower().endswith('.xlsx'):
                    df = pd.read_excel(file_io, engine='openpyxl', sheet_name=0)
                    df1 = pd.read_excel(file_io, engine='openpyxl', sheet_name=1)
                else:
                    df = pd.read_excel(file_io, engine='xlrd', sheet_name=0)
                    df1 = pd.read_excel(file_io, engine='xlrd', sheet_name=1)

                if df.empty or df1.empty:
                    output_results.append({
                        "filename": file_name,
                        "responses": {"error": "Empty Excel file"}
                    })
                    continue

                # Generate DOCX
                docx_file_name = f"{file_name.replace(' ', '_').split('.')[0]}.docx"
                result = analysis_cipl(df, df1, divided_by=divided_by)
                document = create_documents(data=result, filename=docx_file_name)
                docx_buffer = io.BytesIO()
                document.save(docx_buffer)
                docx_buffer.seek(0)

                # Convert DOCX to PDF in-memory
                pdf_file_name = docx_file_name.replace('.docx', '.pdf')
                pdf_buffer = io.BytesIO()
                convert(docx_buffer, pdf_buffer)  # make sure your convert() supports BytesIO
                pdf_buffer.seek(0)

                # Add both files to ZIP
                zipf.writestr(docx_file_name, docx_buffer.getvalue())
                zipf.writestr(pdf_file_name, pdf_buffer.getvalue())

                output_results.append({
                    "filename": file_name,
                    "responses": {"docx": docx_file_name, "pdf": pdf_file_name}
                })

            except Exception as e:
                logging.error(f"Error processing file '{file_name}': {e}")
                raise HTTPException(status_code=500, detail=f"Error processing file '{file_name}': {e}")

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=documents.zip"}
    )

@router.post("/docx3")
async def generate_docx_and_pdf(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    form = await request.form()

    # For simplicity we process only the first file
    # (you can loop later if you want multi-file support)
    if not form:
        raise HTTPException(400, "No file uploaded")

    _, file = next(iter(form.items()))  # first file

    file_bytes = await file.read()
    original_name = file.filename or "input"

    if not original_name.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(415, "Only Excel files (.xlsx, .xls) allowed")

    file_io = io.BytesIO(file_bytes)

    # Read both sheets (adjust engines as needed)
    if original_name.lower().endswith('.xlsx'):
        df  = pd.read_excel(file_io, engine='openpyxl', sheet_name=0)
        df1 = pd.read_excel(file_io, engine='openpyxl', sheet_name=1)
    else:
        df  = pd.read_excel(file_io, engine='xlrd', sheet_name=0)
        df1 = pd.read_excel(file_io, engine='xlrd', sheet_name=1)

    result = analysis_cipl(df, df1, divided_by=divided_by)

    base_name = original_name.rsplit(".", 1)[0].replace(" ", "_")
    docx_name = f"{base_name}.docx"
    pdf_name  = f"{base_name}.pdf"

    # ─── Create DOCX ───────────────────────────────────────
    document = create_documents(data=result, filename=docx_name)
    docx_buffer = io.BytesIO()
    document.save(docx_buffer)
    docx_buffer.seek(0)

    # ─── Create PDF ────────────────────────────────────────
    pdf_buffer = io.BytesIO()
    convert(docx_buffer, pdf_buffer)          # your convert function
    pdf_buffer.seek(0)
    docx_buffer.seek(0)                       # usually needed again

    # ─── Tiny ZIP in memory ────────────────────────────────
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(docx_name, docx_buffer.getvalue())
        zipf.writestr(pdf_name,  pdf_buffer.getvalue())

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type = "application/zip",
        headers = {
            "Content-Disposition": f'attachment; filename="{base_name}_report.zip"'
        }
    )


from spire.doc import *
from spire.doc.common import *
import tempfile


# Assuming these are your existing dependencies / functions
# from your_module import get_db, get_user_permissions_detailed, analysis_cipl, create_documents



# Assuming these are your existing dependencies / functions
# from your_module import get_db, get_user_permissions_detailed, analysis_cipl, create_documents

@router.post("/docx-working")
async def generate_docx_and_pdf(
    request: Request,
    divided_by: Optional[float] = Header(None, convert_underscores=False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    form = await request.form()

    if not form:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Process the first file only (you can extend to multiple later if needed)
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

        # Your business logic
        result = analysis_cipl(df, df1, divided_by=divided_by)

        # Prepare filenames
        base_name = original_filename.rsplit(".", 1)[0].replace(" ", "_").replace(".", "_")
        docx_filename = f"{base_name}.docx"
        pdf_filename = f"{base_name}.pdf"

        # ─── Step 1: Create DOCX in memory ───────────────────────────────
        document = create_documents(data=result, filename=docx_filename)

        docx_buffer = io.BytesIO()
        document.save(docx_buffer)
        docx_buffer.seek(0)

        # ─── Step 2: Convert to PDF using Spire.Doc + temporary files ────
        with tempfile.TemporaryDirectory() as tmp_dir:
            docx_temp_path = os.path.join(tmp_dir, "temp.docx")
            pdf_temp_path = os.path.join(tmp_dir, "temp.pdf")

            # Write DOCX to temp file
            with open(docx_temp_path, "wb") as f:
                f.write(docx_buffer.getvalue())

            # Spire.Doc conversion (using file paths - most stable method)
            spire_doc = Document()
            spire_doc.LoadFromFile(docx_temp_path)
            spire_doc.SaveToFile(pdf_temp_path, FileFormat.PDF)
            spire_doc.Close()

            # Read generated PDF back into memory
            with open(pdf_temp_path, "rb") as f:
                pdf_bytes = f.read()

        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        docx_buffer.seek(0)  # reset in case we want to use it again

        # ─── Step 3: Create small ZIP with both files ────────────────────
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