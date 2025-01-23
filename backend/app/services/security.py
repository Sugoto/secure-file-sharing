import os
import uuid
import base64
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from functools import wraps
from typing import List

SECRET_KEY = os.environ.get("SECRET_KEY", "fallback_very_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ROLES = {
    "admin": ["admin"],
    "user": ["user", "admin"],
    "guest": ["guest", "user", "admin"],
}


def check_roles(required_roles: List[str]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user or "role" not in current_user:
                raise HTTPException(status_code=403, detail="Not authorized")

            user_role = current_user["role"]
            if user_role not in ROLES or not any(
                role in required_roles for role in ROLES[user_role]
            ):
                raise HTTPException(
                    status_code=403, detail="Not authorized for this action"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class SecurityService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    security = HTTPBearer()

    @classmethod
    def hash_password(cls, password: str) -> str:
        return cls.pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def create_access_token(cls, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def decode_token(cls, token: str):
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid token")

    @classmethod
    def get_current_user(
        cls, credentials: HTTPAuthorizationCredentials = Security(security)
    ):
        token = credentials.credentials
        return cls.decode_token(token)

    @staticmethod
    def generate_share_token() -> str:
        """Generate a secure random token for file sharing"""
        return str(uuid.uuid4())


class FileEncryptor:
    @staticmethod
    def generate_key(password: str, salt: bytes = None) -> bytes:
        """Generate encryption key from password"""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    @staticmethod
    def encrypt_file(file_path: str, encryption_key: bytes) -> str:
        """Encrypt file and return encrypted file path"""
        fernet = Fernet(encryption_key)

        with open(file_path, "rb") as file:
            file_data = file.read()

        encrypted_data = fernet.encrypt(file_data)

        encrypted_filename = f"{uuid.uuid4()}_encrypted"
        encrypted_path = os.path.join(os.path.dirname(file_path), encrypted_filename)

        with open(encrypted_path, "wb") as encrypted_file:
            encrypted_file.write(encrypted_data)

        os.remove(file_path)

        return encrypted_path

    @staticmethod
    def decrypt_file(encrypted_path: str, encryption_key: bytes) -> str:
        """Decrypt file and return decrypted file path"""
        fernet = Fernet(encryption_key)

        with open(encrypted_path, "rb") as encrypted_file:
            encrypted_data = encrypted_file.read()

        decrypted_data = fernet.decrypt(encrypted_data)

        decrypted_filename = (
            f"{uuid.uuid4()}_decrypted_{os.path.basename(encrypted_path)}"
        )
        decrypted_path = os.path.join(
            os.path.dirname(encrypted_path), decrypted_filename
        )

        with open(decrypted_path, "wb") as decrypted_file:
            decrypted_file.write(decrypted_data)

        return decrypted_path
