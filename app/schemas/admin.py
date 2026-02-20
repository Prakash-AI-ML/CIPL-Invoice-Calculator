from pydantic import BaseModel, Field
from typing import Optional

class SQLEXecuteRequest(BaseModel):
    sql_query: str = Field(..., description="Raw SQL query to execute (e.g., SELECT * FROM users)")
    personal_password: str = Field(..., description="Enter teh password to execute the query")

class SQLEXecuteResponse(BaseModel):
    executed: bool = Field(..., description="Whether the query was executed")
    results: Optional[list[dict]] = Field(None, description="Query results as list of rows (dicts)")
    row_count: Optional[int] = Field(None, description="Number of rows returned")
    message: str = Field(..., description="Status message")