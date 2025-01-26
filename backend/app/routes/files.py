import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.database import execute_query, fetch_one, fetch_all
from app.services.security import SecurityService, FileEncryptor, check_roles
import base64

router = APIRouter(prefix="/files", tags=["File Management"])

UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


class FileShare(BaseModel):
    file_id: int
    shared_with_username: Optional[str] = None
    permissions: str = "view"  # "view" or "download"
    expires_in_hours: Optional[int] = 24


class FileMetadata(BaseModel):
    filename: str
    file_path: str
    user_id: int
    encrypted_key: str


class ShareLinkCreate(BaseModel):
    file_id: int
    expires_in_hours: Optional[int] = 24


@router.post("/upload")
@check_roles(["user", "admin"])
async def upload_file(
    file: UploadFile = File(...),
    iv: UploadFile = File(...),
    salt: UploadFile = File(...),
    current_user: dict = Depends(SecurityService.get_current_user),
):
    user = fetch_one("SELECT id FROM users WHERE username = ?", (current_user["sub"],))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user[0]

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    # Store the encrypted file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Read IV and salt
    iv_bytes = await iv.read()
    salt_bytes = await salt.read()

    # Store file metadata
    execute_query(
        """INSERT INTO files 
           (filename, user_id, file_path, iv, salt) 
           VALUES (?, ?, ?, ?, ?)""",
        (
            file.filename,
            user_id,
            file_path,
            iv_bytes,
            salt_bytes,
        ),
    )

    return {"message": "File uploaded successfully"}


@router.post("/share")
@check_roles(["user", "admin"])
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

    if not sharer:
        raise HTTPException(status_code=404, detail="User not found")

    expires_at = datetime.utcnow() + timedelta(hours=share_details.expires_in_hours)
    token = (
        None
        if share_details.shared_with_username
        else SecurityService.generate_share_token()
    )

    shared_with_id = None
    if share_details.shared_with_username:
        shared_with = fetch_one(
            "SELECT id FROM users WHERE username = ?",
            (share_details.shared_with_username,),
        )
        if not shared_with:
            raise HTTPException(status_code=404, detail="Shared user not found")
        shared_with_id = shared_with[0]

    execute_query(
        """INSERT INTO file_shares 
           (file_id, shared_by, shared_with, permissions, token, expires_at) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            share_details.file_id,
            sharer[0],
            shared_with_id,
            share_details.permissions,
            token,
            expires_at,
        ),
    )

    return {"message": "File shared successfully", "share_token": token}


@router.get("/list")
@check_roles(["guest", "user", "admin"])
def list_user_files(current_user: dict = Depends(SecurityService.get_current_user)):
    user = fetch_one(
        "SELECT id, role FROM users WHERE username = ?", (current_user["sub"],)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id, user_role = user[0], user[1]

    if user_role == "admin":
        owned_files_raw = fetch_all(
            """
            SELECT f.id, f.filename, f.file_path, f.user_id, u.username as owner_username 
            FROM files f 
            JOIN users u ON f.user_id = u.id
        """
        )
        owned_files = [
            {
                "id": file[0],
                "filename": file[1],
                "file_path": file[2],
                "user_id": file[3],
                "owner_username": file[4],
            }
            for file in owned_files_raw
        ]
        shared_files = []
    else:
        owned_files_raw = fetch_all(
            "SELECT id, filename, file_path, user_id FROM files WHERE user_id = ?",
            (user_id,),
        )
        owned_files = [
            {
                "id": file[0],
                "filename": file[1],
                "file_path": file[2],
                "user_id": file[3],
            }
            for file in owned_files_raw
        ]

        shared_files_raw = fetch_all(
            """
            SELECT f.id, f.filename, f.file_path, f.user_id, fs.permissions
            FROM files f
            JOIN file_shares fs ON f.id = fs.file_id
            WHERE fs.shared_with = ? AND fs.expires_at > CURRENT_TIMESTAMP
            """,
            (user_id,),
        )
        shared_files = [
            {
                "id": file[0],
                "filename": file[1],
                "file_path": file[2],
                "user_id": file[3],
                "permission": file[4],
            }
            for file in shared_files_raw
        ]

    return {"owned_files": owned_files, "shared_files": shared_files}


@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    current_user: dict = Depends(SecurityService.get_current_user),
):
    user = fetch_one(
        "SELECT id, role FROM users WHERE username = ?", (current_user["sub"],)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id, user_role = user[0], user[1]

    if user_role == "admin":
        file = fetch_one("SELECT * FROM files WHERE id = ?", (file_id,))
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
    else:
        file_and_permission = fetch_one(
            """
            SELECT f.*, fs.permissions FROM files f
            LEFT JOIN file_shares fs ON f.id = fs.file_id AND fs.shared_with = ?
            WHERE f.id = ? AND 
            (f.user_id = ? OR 
             (fs.file_id IS NOT NULL AND fs.expires_at > CURRENT_TIMESTAMP))
            """,
            (user_id, file_id, user_id),
        )

        if not file_and_permission:
            raise HTTPException(status_code=403, detail="Access denied")

        if file_and_permission[-1] == "view":
            raise HTTPException(status_code=403, detail="Download not permitted")

        file = file_and_permission[:-1]

    file = fetch_one("SELECT filename, file_path, iv, salt FROM files WHERE id = ?", (file_id,))
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    filename, file_path, iv, salt = file

    # Ensure proper base64 encoding without line breaks or whitespace
    headers = {
        "X-IV": base64.b64encode(iv).decode('utf-8').strip(),
        "X-Salt": base64.b64encode(salt).decode('utf-8').strip(),
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "X-IV, X-Salt"  # Important for CORS
    }

    return FileResponse(
        file_path,
        headers=headers,
        media_type="application/octet-stream"
    )


@router.delete("/delete/{file_id}")
@check_roles(["user", "admin"])
async def delete_file(
    file_id: int, current_user: dict = Depends(SecurityService.get_current_user)
):
    user = fetch_one(
        "SELECT id, role FROM users WHERE username = ?", (current_user["sub"],)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id, user_role = user[0], user[1]

    if user_role == "admin":
        file = fetch_one("SELECT * FROM files WHERE id = ?", (file_id,))
    else:
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


@router.get("/shared/{token}")
def access_shared_file(token: str, password: str):
    file_data = fetch_one(
        """
        SELECT f.* FROM files f
        JOIN file_shares fs ON f.id = fs.file_id
        WHERE fs.token = ? AND fs.expires_at > CURRENT_TIMESTAMP
        """,
        (token,),
    )

    if not file_data:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")

    try:
        stored_key = base64.urlsafe_b64decode(file_data[4])
        salt = base64.urlsafe_b64decode(file_data[5])

        derived_key, _ = FileEncryptor.generate_key(password, salt)
        decrypted_path = FileEncryptor.decrypt_file(file_data[3], derived_key)

        def cleanup(decrypted_path=decrypted_path):
            try:
                os.remove(decrypted_path)
            except:
                pass

        return FileResponse(
            decrypted_path,
            filename=file_data[1],
            background=cleanup,
            media_type="application/octet-stream",
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Decryption failed. Check your password."
        )


@router.delete("/revoke-share/{share_id}")
def revoke_share(
    share_id: int, current_user: dict = Depends(SecurityService.get_current_user)
):
    user = fetch_one("SELECT id FROM users WHERE username = ?", (current_user["sub"],))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    share = fetch_one(
        """
        SELECT fs.* FROM file_shares fs
        JOIN files f ON fs.file_id = f.id
        WHERE fs.id = ? AND f.user_id = ?
        """,
        (share_id, user[0]),
    )

    if not share:
        raise HTTPException(
            status_code=403, detail="Not authorized to revoke this share"
        )

    execute_query("DELETE FROM file_shares WHERE id = ?", (share_id,))
    return {"message": "Share access revoked successfully"}
