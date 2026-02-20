import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession 

from app.api.dependencies import get_user_permissions_detailed
from app.core.config import settings
from app.db.session import get_db
from app.schemas.admin import SQLEXecuteRequest, SQLEXecuteResponse 
from app.models.user import UserRole

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sql-execute", response_model=SQLEXecuteResponse, tags=["admin"])
async def execute_sql_query(
    request: SQLEXecuteRequest,
    current_user: dict = Depends(get_user_permissions_detailed),
    db: AsyncSession = Depends(get_db)
):
    # Additional check: Only allow muhun username
    if "muhun" != current_user.get("username"):
        logger.warning(f"Unauthorized SQL attempt by {current_user.get('username', 'unknown')} ({current_user.get('role')})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Username mismatch"
        )

    if not request.personal_password == settings.personal_password: 
        logger.info(f"SQL execution skipped by {current_user['username']} (personal_password mismatch)")
        return SQLEXecuteResponse(
            executed=False,
            results=None,
            row_count=0,
            message="Query not executed (personal_password mismatch)"
        )

    # Use explicit session for full control (commit/rollback for DML/DDL)

    try:
        logger.info(f"Executing SQL by {current_user['username']}: {request.sql_query[:100]}...")  # Log truncated query
        
        result = await db.execute(text(request.sql_query))
        
        # For SELECT-like queries: fetch results
        try:
            rows = result.fetchall()
            row_count = len(rows)
            results = [dict(row._mapping) for row in rows] if rows else []
            query_type = "SELECT" if request.sql_query.strip().upper().startswith('SELECT') else "DML/DDL"
            logger.info(f"SQL executed successfully by {current_user['username']}: {row_count} rows returned ({query_type})")
            await db.commit()
            return SQLEXecuteResponse(
                executed=True,
                results=results,
                row_count=row_count,
                message=f"Query executed successfully ({row_count} rows returned)"
            )
        except Exception as fetch_err:
            # For non-SELECT (INSERT/UPDATE/DELETE/ALTER/CREATE/TRUNCATE): use rowcount
            affected_rows = result.rowcount
            query_type = "DML/DDL"
            logger.info(f"SQL executed successfully by {current_user['username']}: {affected_rows} rows affected ({query_type})")
            await db.commit()
            return SQLEXecuteResponse(
                executed=True,
                results=None,  # No results for DML/DDL
                row_count=affected_rows,
                message=f"Query executed successfully ({affected_rows} rows affected)"
            )
            
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"SQL execution failed by {current_user['username']}: {str(e)} | Query: {request.sql_query}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error in SQL execution by {current_user['username']}: {str(e)} | Query: {request.sql_query}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during execution"
        )