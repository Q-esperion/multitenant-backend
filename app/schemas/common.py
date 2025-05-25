from typing import TypeVar, Generic, Optional, List, Any
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
import pytz
from app.core.config import settings

T = TypeVar('T')

# class PageResponse(BaseModel, Generic[T]):
#     items: List[T]
#     total: int
#     page: int
#     page_size: int

class BaseSchema(BaseModel):
    """基础模型类，统一处理日期时间的序列化"""
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None,
            date: lambda d: d.isoformat() if d else None
        }
    )

class ResponseModel(BaseModel):
    code: int = 200
    msg: Optional[str] = "OK"
    data: Optional[Any] = None

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda dt: dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None,
            date: lambda d: d.isoformat() if d else None
        }
    )

class Success(ResponseModel):
    """成功响应"""
    pass

class Fail(JSONResponse):
    def __init__(
        self,
        code: int = 400,
        msg: Optional[str] = None,
        data: Optional[Any] = None,
        **kwargs,
    ):
        content = ResponseModel(
            code=code,
            msg=msg,
            data=data,
            **kwargs
        ).model_dump()
        super().__init__(content=content, status_code=code)

class SuccessExtra(ResponseModel):
    """带分页信息的成功响应"""
    total: int
    page: int
    page_size: int 