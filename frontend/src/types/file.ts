export type FileData = [
  number, // id
  string, // filename
  number, // user_id
  string, // file_path
  string, // encryption_key
  string, // iv
  string // created_at
];

export interface FileListResponse {
  owned_files: FileData[];
  shared_files: FileData[];
}

export interface FileShareRequest {
  fileId: number;
  recipientUsername: string;
}

export interface FileInfo {
  id: number;
  filename: string;
}
