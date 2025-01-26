import { create } from "zustand";
import { fileService } from "../services/fileService";
import { File, FileShareRequest, ShareResponse } from "../types/file";

interface FileStore {
  ownedFiles: File[];
  sharedFiles: File[];
  isLoading: boolean;
  error: string | null;
  fetchFiles: () => Promise<void>;
  deleteFile: (id: number) => Promise<void>;
  uploadFile: (file: Blob, password: string) => Promise<void>;
  shareFile: (request: FileShareRequest) => Promise<ShareResponse | undefined>;
}

interface ShareData {
  file_id: number;
  shared_with_username?: string;
  permissions: "view" | "download";
  expires_in_hours: number;
}

interface ShareResponse {
  message: string;
  share_token?: string;
}

export const useFileStore = create<FileStore>((set) => ({
  ownedFiles: [],
  sharedFiles: [],
  isLoading: false,
  error: null,

  fetchFiles: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fileService.listFiles();
      set({
        ownedFiles: response.owned_files || [],
        sharedFiles: response.shared_files || [],
        isLoading: false,
      });
    } catch (error) {
      set({ error: "Failed to fetch files", isLoading: false });
    }
  },

  deleteFile: async (id: number) => {
    try {
      await fileService.deleteFile(id);
      set((state) => ({
        ownedFiles: state.ownedFiles.filter((file) => file.id !== id),
        sharedFiles: state.sharedFiles.filter((file) => file.id !== id),
      }));
    } catch (error) {
      set({ error: "Failed to delete file" });
    }
  },

  uploadFile: async (file: Blob, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await fileService.uploadFile(file, password);
      const response = await fileService.listFiles();
      set({
        ownedFiles: response.owned_files || [],
        sharedFiles: response.shared_files || [],
        isLoading: false,
      });
    } catch (error) {
      set({ error: "Failed to upload file", isLoading: false });
    }
  },

  shareFile: async (shareData: ShareData): Promise<ShareResponse> => {
    try {
      const response = await fileService.shareFile(shareData);
      set({ error: null });
      return response;
    } catch (error) {
      set({ error: "Failed to share file" });
      throw error;
    }
  },
}));
