import os
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from app.services.database import execute_query, fetch_one, fetch_all
from app.services.security import SecurityService, check_roles
from app.models import FileShare
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

router = APIRouter(prefix="/files", tags=["File Management"])

UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

SERVER_KEY = os.getenv("SERVER_KEY", os.urandom(32))


def encrypt_file(data: bytes, iv: bytes) -> bytes:
    if len(iv) != 12:
        raise ValueError("IV must be 12 bytes long for AES GCM mode")

    aesgcm = AESGCM(SERVER_KEY)
    return aesgcm.encrypt(iv, data, None)


def decrypt_file(encrypted_data: bytes, iv: bytes) -> bytes:
    aesgcm = AESGCM(SERVER_KEY)
    return aesgcm.decrypt(iv, encrypted_data, None)


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

    iv_bytes = await iv.read()
    if len(iv_bytes) != 12:
        raise HTTPException(
            status_code=400, detail="Invalid IV size. Must be 12 bytes for AES GCM mode"
        )

    with open(file_path, "wb") as buffer:
        content = await file.read()
        try:
            encrypted_content = encrypt_file(content, iv_bytes)
            buffer.write(encrypted_content)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    salt_bytes = await salt.read()

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

    file = fetch_one(
        "SELECT filename, file_path, iv, salt FROM files WHERE id = ?", (file_id,)
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    filename, file_path, iv, salt = file

    headers = {
        "X-IV": base64.b64encode(iv).decode("utf-8").strip(),
        "X-Salt": base64.b64encode(salt).decode("utf-8").strip(),
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "X-IV, X-Salt",
    }

    with open(file_path, "rb") as f:
        encrypted_content = f.read()
        decrypted_content = decrypt_file(encrypted_content, iv)

    return Response(
        content=decrypted_content,
        headers=headers,
        media_type="application/octet-stream",
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
        SELECT f.filename, f.file_path, f.iv, f.salt 
        FROM files f
        JOIN file_shares fs ON f.id = fs.file_id
        WHERE fs.token = ? AND fs.expires_at > CURRENT_TIMESTAMP
        """,
        (token,),
    )

    if not file_data:
        raise HTTPException(status_code=404, detail="Invalid or expired share link")

    filename, file_path, iv, salt = file_data

    headers = {
        "X-IV": base64.b64encode(iv).decode("utf-8").strip(),
        "X-Salt": base64.b64encode(salt).decode("utf-8").strip(),
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "X-IV, X-Salt, Content-Disposition",
    }

    with open(file_path, "rb") as f:
        encrypted_content = f.read()
        decrypted_content = decrypt_file(encrypted_content, iv)

    return Response(
        content=decrypted_content,
        headers=headers,
        media_type="application/octet-stream",
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
