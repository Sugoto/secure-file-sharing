import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from pydantic import BaseModel

from app.services.database import execute_query, fetch_one, fetch_all
from app.services.security import SecurityService, FileEncryptor
import base64

router = APIRouter(prefix="/files", tags=["File Management"])

UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


class FileShare(BaseModel):
    file_id: int
    shared_with_username: str
    permissions: str = "view"
    expires_at: Optional[datetime] = None


class FileMetadata(BaseModel):
    filename: str
    file_path: str
    user_id: int
    encrypted_key: str


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    password: str = Form(...),
    current_user: dict = Depends(SecurityService.get_current_user),
):
    user = fetch_one("SELECT id FROM users WHERE username = ?", (current_user["sub"],))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user[0]

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    encryption_key, salt = FileEncryptor.generate_key(password)

    try:
        encrypted_path = FileEncryptor.encrypt_file(file_path, encryption_key)

        execute_query(
            "INSERT INTO files (filename, user_id, file_path, encrypted_key, encryption_salt) VALUES (?, ?, ?, ?, ?)",
            (
                file.filename,
                user_id,
                encrypted_path,
                base64.urlsafe_b64encode(encryption_key).decode(),
                base64.urlsafe_b64encode(salt).decode(),
            ),
        )

        return {
            "filename": file.filename,
            "message": "File uploaded and encrypted successfully",
        }

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")


@router.post("/share")
def share_file(
    share_details: FileShare,
    current_user: dict = Depends(SecurityService.get_current_user),
):
    file = fetch_one("SELECT * FROM files WHERE id = ?", (share_details.file_id,))
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    sharer = fetch_one(
        "SELECT id FROM users WHERE username = ?", (current_user["sub"],)
    )
    shared_with = fetch_one(
        "SELECT id FROM users WHERE username = ?", (share_details.shared_with_username,)
    )

    if not sharer or not shared_with:
        raise HTTPException(status_code=404, detail="User not found")

    expires_at = share_details.expires_at or datetime.utcnow() + timedelta(days=7)

    execute_query(
        "INSERT INTO file_shares (file_id, shared_by, shared_with, permissions, expires_at) VALUES (?, ?, ?, ?, ?)",
        (
            share_details.file_id,
            sharer[0],
            shared_with[0],
            share_details.permissions,
            expires_at,
        ),
    )

    return {"message": "File shared successfully"}


@router.get("/list")
def list_user_files(current_user: dict = Depends(SecurityService.get_current_user)):
    user = fetch_one("SELECT id FROM users WHERE username = ?", (current_user["sub"],))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user[0]

    owned_files = fetch_all("SELECT * FROM files WHERE user_id = ?", (user_id,))

    shared_files = fetch_all(
        """
        SELECT f.* FROM files f
        JOIN file_shares fs ON f.id = fs.file_id
        WHERE fs.shared_with = ? AND fs.expires_at > CURRENT_TIMESTAMP
        """,
        (user_id,),
    )

    return {"owned_files": owned_files, "shared_files": shared_files}


@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    password: str,
    current_user: dict = Depends(SecurityService.get_current_user),
):
    user = fetch_one("SELECT id FROM users WHERE username = ?", (current_user["sub"],))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user[0]

    file = fetch_one(
        """
        SELECT * FROM files 
        WHERE id = ? AND 
        (user_id = ? OR 
         id IN (SELECT file_id FROM file_shares WHERE shared_with = ? AND expires_at > CURRENT_TIMESTAMP))
        """,
        (file_id, user_id, user_id),
    )

    if not file:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        stored_key = base64.urlsafe_b64decode(file[4])
        salt = base64.urlsafe_b64decode(file[5])

        derived_key, _ = FileEncryptor.generate_key(password, salt)

        decrypted_path = FileEncryptor.decrypt_file(file[3], derived_key)

        return {"filename": file[1], "file_path": decrypted_path}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Decryption failed. Check your password."
        )


@router.delete("/delete/{file_id}")
def delete_file(
    file_id: int, current_user: dict = Depends(SecurityService.get_current_user)
):
    user = fetch_one("SELECT id FROM users WHERE username = ?", (current_user["sub"],))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user[0]

    file = fetch_one(
        "SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, user_id)
    )
    if not file:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this file"
        )

    try:
        os.remove(file[3])
    except FileNotFoundError:
        pass

    execute_query("DELETE FROM file_shares WHERE file_id = ?", (file_id,))
    execute_query("DELETE FROM files WHERE id = ?", (file_id,))

    return {"message": "File deleted successfully"}
