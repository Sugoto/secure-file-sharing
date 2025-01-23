import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from pydantic import BaseModel

from app.services.database import execute_query, fetch_one, fetch_all
from app.services.security import SecurityService

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
    current_user: dict = Depends(SecurityService.get_current_user),
):
    user = fetch_one("SELECT id FROM users WHERE username = ?", (current_user["sub"],))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user[0]

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    execute_query(
        "INSERT INTO files (filename, user_id, file_path, encrypted_key) VALUES (?, ?, ?, ?)",
        (file.filename, user_id, file_path, "placeholder_encrypted_key"),
    )

    return {"filename": file.filename, "message": "File uploaded successfully"}


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
    file_id: int, current_user: dict = Depends(SecurityService.get_current_user)
):
    user = fetch_one("SELECT id FROM users WHERE username = ?", (current_user["sub"],))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user[0]

    file = fetch_one(
        """
        SELECT f.* FROM files f
        LEFT JOIN file_shares fs ON f.id = fs.file_id
        WHERE (f.user_id = ? OR 
               (fs.shared_with = ? AND fs.expires_at > CURRENT_TIMESTAMP))
        AND f.id = ?
        """,
        (user_id, user_id, file_id),
    )

    if not file:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"filename": file[1], "file_path": file[3], "encrypted_key": file[4]}


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
