from typing import Optional
from pydantic import BaseModel, EmailStr


class FileShare(BaseModel):
    file_id: int
    shared_with_username: Optional[str] = None
    permissions: str = "view"
    expires_in_hours: Optional[int] = 24


class FileMetadata(BaseModel):
    filename: str
    file_path: str
    user_id: int
    encrypted_key: str


class ShareLinkCreate(BaseModel):
    file_id: int
    expires_in_hours: Optional[int] = 24


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"
    mfa_enabled: Optional[bool] = False


class UserLogin(BaseModel):
    username: str
    password: str


class MFAVerify(BaseModel):
    username: str
    code: str


class UserRoleUpdate(BaseModel):
    role: str
