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
  permission?: "view" | "download";
}

export interface FileListResponse {
  owned_files: File[];
  shared_files: File[];
}

export interface FileShareRequest {
  file_id: number;
  shared_with_username?: string;
  permissions: "view" | "download";
  expires_in_hours?: number;
}

export interface ShareResponse {
  share_token: string;
}

export interface FileInfo {
  id: number;
  filename: string;
}
