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
    """
    Decorator to check if the current user has the required roles.

    Args:
        required_roles (List[str]): List of roles that are allowed to access the endpoint

    Returns:
        Callable: Decorated function that checks user roles before execution
    """

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
    """Service class for handling security-related operations like password hashing and JWT tokens."""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    security = HTTPBearer()

    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password (str): Plain text password

        Returns:
            str: Hashed password
        """
        return cls.pwd_context.hash(password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password (str): Plain text password to verify
            hashed_password (str): Hashed password to compare against

        Returns:
            bool: True if password matches, False otherwise
        """
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def create_access_token(cls, data: dict) -> str:
        """
        Create a JWT access token.

        Args:
            data (dict): Payload data to encode in the token

        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @classmethod
    def decode_token(cls, token: str):
        """
        Decode and validate a JWT token.

        Args:
            token (str): JWT token to decode

        Returns:
            dict: Decoded token payload

        Raises:
            HTTPException: If token is invalid
        """
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid token")

    @classmethod
    def get_current_user(
        cls, credentials: HTTPAuthorizationCredentials = Security(security)
    ):
        """
        Get the current authenticated user from the request.

        Args:
            credentials (HTTPAuthorizationCredentials): Bearer token credentials

        Returns:
            dict: Current user information

        Raises:
            HTTPException: If authentication fails
        """
        token = credentials.credentials
        return cls.decode_token(token)

    @staticmethod
    def generate_share_token() -> str:
        """
        Generate a secure random token for file sharing.

        Returns:
            str: UUID-based share token
        """
        return str(uuid.uuid4())


class FileEncryptor:
    """Class for handling file encryption and decryption operations."""

    @staticmethod
    def generate_key(password: str, salt: bytes = None) -> bytes:
        """
        Generate an encryption key from a password using PBKDF2.

        Args:
            password (str): Password to derive key from
            salt (bytes, optional): Salt for key derivation. Generated if None.

        Returns:
            tuple: (derived_key, salt) pair
        """
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
        """
        Encrypt a file using Fernet symmetric encryption.

        Args:
            file_path (str): Path to the file to encrypt
            encryption_key (bytes): Key to use for encryption

        Returns:
            str: Path to the encrypted file

        Note:
            Original file is deleted after encryption
        """
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
        """
        Decrypt a file using Fernet symmetric encryption.

        Args:
            encrypted_path (str): Path to the encrypted file
            encryption_key (bytes): Key to use for decryption

        Returns:
            str: Path to the decrypted file

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
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
