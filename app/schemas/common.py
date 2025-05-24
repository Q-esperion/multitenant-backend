from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')

class Success(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

class Error(BaseModel):
    code: int = 400
    message: str = "error"
    detail: Optional[str] = None 