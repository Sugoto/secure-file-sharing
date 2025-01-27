# SecureShare

A secure end-to-end encrypted file sharing application with user management and granular access controls.

## Features

- **End-to-End Encryption**: Files are encrypted client-side using AES-GCM before upload
- **Secure File Sharing**: Share files with specific users or via secure links
- **User Management**: Role-based access control (Admin/User/Guest)
- **Security Features**:
  - Multi-factor authentication support
  - File access permissions (view/download)
  - Expiring share links
  - Input sanitization
  - Encrypted data at rest

## Tech Stack

### Frontend

- React + TypeScript
- Tailwind CSS
- Zustand for state management
- Web Crypto API for client-side encryption

### Backend

- FastAPI (Python)
- SQLite database
- JWT authentication
- AESGCM encryption

## Running with Docker

```sh
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000/docs

## Development

### Backend Setup

```sh
cd backend
pip install -r requirements.txt
python -m pytest
```

### Frontend Setup

```sh
cd frontend
pnpm install
pnpm dev
```

## Security

- Files are encrypted using AES-GCM before upload
- Unique IV (Initialization Vector) per file
- Password-based key derivation with salting
- Encrypted file storage
- Sanitized user inputs
- Role-based access control
- MFA support

## API Endpoints

### Authentication
- `/auth/register` - Register new user
- `/auth/login` - User login
- `/auth/verify-mfa` - Verify MFA code
- `/auth/toggle-mfa` - Toggle MFA for current user
- `/auth/validate-token` - Validate JWT token
- `/auth/account` - Delete current user's account
- `/auth/users` - List all users (admin only)
- `/auth/users/{user_id}/role` - Update user role (admin only)
- `/auth/users/{user_id}` - Delete user (admin only)

### Files
- `/files/upload` - Upload encrypted files
- `/files/download/{file_id}` - Download files 
- `/files/share` - Share files with users
- `/files/shared/{token}` - Access shared files
- `/files/list` - List user's files

## License

[MIT License](LICENSE)
