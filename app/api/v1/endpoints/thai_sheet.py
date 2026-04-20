from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
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

import traceback
import tempfile

# ─── FastAPI app ────────────────────────────────────────

router = APIRouter() 



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



