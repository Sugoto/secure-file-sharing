export interface FileMetadata {
  id: number;
  filename: string;
  file_path: string;
  user_id: number;
  created_at: string;
}

export interface FileUploadResponse {
  filename: string;
  message: string;
}

export interface FileListResponse {
  owned_files: FileMetadata[];
  shared_files: FileMetadata[];
}

export interface FileShareRequest {
  file_id: number;
  shared_with_username?: string;
  permissions?: string;
  expires_in_hours?: number;
}
