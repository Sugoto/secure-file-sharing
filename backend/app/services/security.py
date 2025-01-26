import os
import uuid
import base64
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from functools import wraps
from typing import List
import random
import string
from email.message import EmailMessage
import smtplib
import asyncio

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
        def sync_wrapper(*args, **kwargs):
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

            return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
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

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

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

    @staticmethod
    def generate_mfa_code() -> str:
        """
        Generate a 6-digit MFA code.

        Returns:
            str: 6-digit MFA code
        """
        return "".join(random.choices(string.digits, k=6))

    @staticmethod
    def send_mfa_code(email: str, code: str):
        """
        Send MFA code via email.

        Args:
            email (str): Email address to send the code to
            code (str): 6-digit MFA code

        Note:
            Uses SMTP settings from environment variables
        """
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_password = os.environ.get("SMTP_PASSWORD")

        msg = EmailMessage()
        msg.set_content(f"Your MFA code is: {code}")
        msg["Subject"] = "Your MFA Code"
        msg["From"] = smtp_user
        msg["To"] = email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
