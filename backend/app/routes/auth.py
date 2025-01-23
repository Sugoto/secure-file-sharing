from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.services.database import execute_query, fetch_one
from app.services.security import SecurityService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"


class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/register")
def register_user(user: UserCreate):
    existing_user = fetch_one(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (user.username, user.email),
    )

    if existing_user:
        raise HTTPException(
            status_code=400, detail="Username or email already registered"
        )

    hashed_password = SecurityService.hash_password(user.password)

    try:
        execute_query(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            (user.username, user.email, hashed_password, user.role),
        )
        return {"message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login")
def login_user(user: UserLogin):
    db_user = fetch_one("SELECT * FROM users WHERE username = ?", (user.username,))

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not SecurityService.verify_password(user.password, db_user[3]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = SecurityService.create_access_token(
        data={"sub": user.username, "role": db_user[4]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"username": db_user[1], "email": db_user[2], "role": db_user[4]},
    }


@router.get("/validate-token")
def validate_token(token_data: dict = Depends(SecurityService.get_current_user)):
    return {"valid": True, "user": token_data}
