import { create } from "zustand";
import { fileService } from "../services/fileService";
import { FileData, FileInfo } from "../types/file";

interface FileStore {
  ownedFiles: FileInfo[];
  sharedFiles: FileInfo[];
  isLoading: boolean;
  error: string | null;
  fetchFiles: () => Promise<void>;
  deleteFile: (fileId: number) => Promise<void>;
  uploadFile: (file: File, password: string) => Promise<void>;
}

const mapFileDataToInfo = (fileData: FileData): FileInfo => ({
  id: fileData[0],
  filename: fileData[1],
});

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
        ownedFiles: response.owned_files.map(mapFileDataToInfo),
        sharedFiles: response.shared_files.map(mapFileDataToInfo),
        isLoading: false,
      });
    } catch (error) {
      set({ error: "Failed to fetch files", isLoading: false });
    }
  },
  deleteFile: async (fileId: number) => {
    try {
      await fileService.deleteFile(fileId);
      set((state) => ({
        ownedFiles: state.ownedFiles.filter((file) => file.id !== fileId),
        sharedFiles: state.sharedFiles.filter((file) => file.id !== fileId),
      }));
    } catch (error) {
      set({ error: "Failed to delete file" });
    }
  },
  uploadFile: async (file: File, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await fileService.uploadFile(file, password);
      set({ isLoading: false });
      const response = await fileService.listFiles();
      set({
        ownedFiles: response.owned_files.map(mapFileDataToInfo),
        sharedFiles: response.shared_files.map(mapFileDataToInfo),
      });
    } catch (error) {
      set({ error: "Failed to upload file", isLoading: false });
    }
  },
}));
