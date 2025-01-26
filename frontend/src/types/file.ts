export type FileData = [
  number, // id
  string, // filename
  number, // user_id
  string, // file_path
  string, // encryption_key
  string, // iv
  string // created_at
];

export interface File {
  id: number;
  filename: string;
  file_path: string;
  user_id: number;
  encryption_key: string;
  iv: string;
  created_at: string;
  owner_username?: string;
}

export interface FileListResponse {
  owned_files: File[];
  shared_files: File[];
}

export interface ShareRequest {
  file_id: number;
  shared_with_username?: string;
  expires_in_hours?: number;
}

export interface ShareResponse {
  share_token: string;
}

export interface FileInfo {
  id: number;
  filename: string;
}
