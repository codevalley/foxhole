from pydantic import BaseModel
from typing import List, Optional


class ErrorDetail(BaseModel):
    loc: List[str]
    msg: str
    type: str


class ErrorResponse(BaseModel):
    detail: List[ErrorDetail]
    message: Optional[str] = None
