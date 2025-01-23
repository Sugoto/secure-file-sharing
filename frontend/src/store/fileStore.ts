import { create } from 'zustand';
import { FileMetadata } from '../types/file';
import { fileService } from '../services/fileService';

interface FileState {
  ownedFiles: FileMetadata[];
  sharedFiles: FileMetadata[];
  isLoading: boolean;
  error: string | null;
  fetchFiles: () => Promise<void>;
  uploadFile: (file: File, password: string) => Promise<void>;
  deleteFile: (fileId: number) => Promise<void>;
}

export const useFileStore = create<FileState>((set) => ({
  ownedFiles: [],
  sharedFiles: [],
  isLoading: false,
  error: null,

  fetchFiles: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fileService.listFiles();
      set({
        ownedFiles: response.owned_files,
        sharedFiles: response.shared_files,
        isLoading: false,
      });
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch files', isLoading: false });
    }
  },

  uploadFile: async (file: File, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await fileService.uploadFile(file, password);
      const response = await fileService.listFiles();
      set({
        ownedFiles: response.owned_files,
        sharedFiles: response.shared_files,
        isLoading: false,
      });
    } catch (error) {
      set({ error: 'Failed to upload file', isLoading: false });
    }
  },

  deleteFile: async (fileId: number) => {
    set({ isLoading: true, error: null });
    try {
      await fileService.deleteFile(fileId);
      const response = await fileService.listFiles();
      set({
        ownedFiles: response.owned_files,
        sharedFiles: response.shared_files,
        isLoading: false,
      });
    } catch (error) {
      set({ error: 'Failed to delete file', isLoading: false });
    }
  },
}));
