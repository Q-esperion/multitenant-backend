from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class JWTPayload(BaseModel):
    user_id: int
    username: str
    is_superuser: bool
    tenant_id: Optional[int] = None
    exp: datetime

class JWTOut(BaseModel):
    access_token: str
    username: str
    tenant_id: Optional[int] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    tenant_id: Optional[int] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None 