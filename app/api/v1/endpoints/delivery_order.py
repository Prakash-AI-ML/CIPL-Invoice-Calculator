
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

import uuid
from typing import List, Dict
import io
import base64
import pandas as pd
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, UploadFile, Request, HTTPException, Header
from typing import List, Optional
from docx2pdf import convert
import os
import tempfile
import json
import logging
from datetime import datetime
from app.delivery_order.documents import get_deliver_order
from app.db.session import get_db
from app.api.dependencies import get_user_permissions_detailed
from app.crud.log_manage import backend_logs
from app.schemas.delivery_order import LogisticsDocument



# Setup logger for this module
logger = logging.getLogger(__name__)

router = APIRouter() 

@router.post("/docx")
async def Delivery_Order(
    request: Request,
    data: LogisticsDocument,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    # # # 🔐 Backend safety check (DO NOT rely only on frontend)
    # if not current_user.get("can_impersonate") and not current_user.get("impersonated"):
    #     raise HTTPException(status_code=403, detail="Permission denied")
    data = data.model_dump()
    description = f"Delivery Order Document generator accessed by authenticated user: {current_user['username']} "
    action = 'Delivery Order Document generator'
    await backend_logs(request = request, current_user= current_user, endpoint='/api/v1/do/docx',
                        action= action, description= description, is_backend= True, input_params= data)
    

    
        
    try:
            document = get_deliver_order(data)
            # Save to memory buffer
            buffer = io.BytesIO()
            document.save(buffer)
            buffer.seek(0)

            # Return as response
            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                # media_type="application/docx",
                headers={
                    "Content-Disposition": f"attachment; filename=do-ref.docx"
                }
            )
            # clean_result = jsonable_encoder(result)

            output_results.append({
                "filename": file_name,
                "responses": result
            })

    except Exception as e:
        logging.error(f"Error processing file : {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")

    return JSONResponse(content=output_results)





@router.post("/docx1")
async def Delivery_Order(
    request: Request,
    data: LogisticsDocument,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed),
):
    try:
        data_dict = data.model_dump()
        document = get_deliver_order(data_dict)

        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, "delivery.docx")
            pdf_path = os.path.join(tmpdir, "delivery.pdf")

            # Save DOCX to disk
            document.save(docx_path)

            # Convert DOCX → PDF
            convert(docx_path, pdf_path)

            # Read PDF into memory
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

        # Return PDF as preview
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline; filename=delivery-note.pdf"
            }
        )

    except Exception as e:
        logging.error(f"Error processing file : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-delivery-note")
async def generate_delivery_note(request: Request,
    data: LogisticsDocument,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_user_permissions_detailed), ):
    try:
        doc = get_deliver_order(data.model_dump())  # your function → python-docx Document

        # DOCX buffer
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)
        # docx_base64 = base64.b64encode(docx_buffer.read()).decode("utf-8")

        # PDF conversion in memory
        # pdf_buffer = io.BytesIO()
        # docx_buffer.seek(0)  # reset for converter
        # convert(docx_buffer, pdf_buffer)  # docx2pdf supports file-like objects
        # pdf_buffer.seek(0)
        # # pdf_base64 = base64.b64encode(pdf_buffer.read()).decode("utf-8")

        return StreamingResponse(
        docx_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="Delivery-Note-{data["ref_no"]}.pdf"'
        }
    )

        return JSONResponse({
            "status": "success",
            "docx": {
                "filename": f"Delivery-Note-{data.ref_no}.docx",
                "base64": docx_base64,
                "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            },
            "pdf": {
                "filename": f"Delivery-Note-{data.ref_no}.pdf",
                "base64": pdf_base64,
                "mime": "application/pdf"
            }
        })

    except Exception as e:
        raise HTTPException(500, detail=str(e))