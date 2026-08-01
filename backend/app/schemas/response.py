from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")

class ApiResponse(BaseModel, Generic[DataT]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[DataT] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str
    details: Optional[dict] = Field(default_factory=dict)
