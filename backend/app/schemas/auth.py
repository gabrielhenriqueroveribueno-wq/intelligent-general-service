from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class UserMe(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: str | None = None
    must_change_password: bool = False

    class Config:
        from_attributes = True
