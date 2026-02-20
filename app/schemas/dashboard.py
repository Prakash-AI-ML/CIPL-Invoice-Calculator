from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal
from datetime import datetime

class CashFlowRequest(BaseModel):
    filter: Optional[Literal[
        "last_12_months",
        "this_fy",
        "previous_fy",
        "all",
    ]] = Field(
        default="last_12_months",
        description="Time range used to calculate cash flow",
    )



class CashFlowFilter(BaseModel):
    year: Optional[int] = Field(
        None,
        description="Year must be between 2018 and current year. If omitted, overall analysis is shown."
    )
    quarter: Optional[Literal["q1", "q2", "q3", "q4"]] = None

    @model_validator(mode="after")
    def validate_filters(self):
        current_year = datetime.now().year

        # Quarter without year is not allowed
        if self.quarter and self.year is None:
            raise ValueError("Quarter cannot be used without specifying a year")

        # Validate year only if provided
        if self.year is not None:
            if self.year < 2018 or self.year > current_year:
                raise ValueError(
                    f"year must be between 2018 and {current_year}"
                )

        return self