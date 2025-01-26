import { axiosInstance } from "../config/axios";
import { FileListResponse, FileShareRequest } from "../types/file";

class FileService {
  async uploadFile(file: File, password: string) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("password", password);

    const response = await axiosInstance.post("/files/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  }

  async listFiles(): Promise<FileListResponse> {
    const response = await axiosInstance.get("/files/list");
    return response.data;
  }

  async downloadFile(fileId: number, password?: string) {
    const url = `/files/download/${fileId}`;
    const queryParams = password ? `?password=${password}` : "";
    const response = await axiosInstance.get(url + queryParams, {
      responseType: "blob",
    });
    return response.data;
  }

  async shareFile(shareDetails: FileShareRequest) {
    const response = await axiosInstance.post("/files/share", shareDetails);
    return response.data;
  }

  async deleteFile(fileId: number) {
    const response = await axiosInstance.delete(`/files/delete/${fileId}`);
    return response.data;
  }

  async accessSharedFile(token: string, password: string): Promise<Blob> {
    const response = await axiosInstance.get(
      `/files/shared/${token}?password=${password}`,
      {
        responseType: "blob",
      }
    );
    return response.data;
  }
}

export const fileService = new FileService();
