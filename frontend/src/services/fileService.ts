import { axiosInstance } from "../config/axios";
import { FileListResponse, FileShareRequest } from "../types/file";

class FileEncryption {
  static async generateKey(
    password: string,
    salt?: Uint8Array
  ): Promise<[CryptoKey, Uint8Array]> {
    const enc = new TextEncoder();
    const passwordBuffer = enc.encode(password);

    if (!salt) {
      salt = crypto.getRandomValues(new Uint8Array(16));
    }

    const keyMaterial = await crypto.subtle.importKey(
      "raw",
      passwordBuffer,
      "PBKDF2",
      false,
      ["deriveBits", "deriveKey"]
    );

    const key = await crypto.subtle.deriveKey(
      {
        name: "PBKDF2",
        salt,
        iterations: 100000,
        hash: "SHA-256",
      },
      keyMaterial,
      { name: "AES-GCM", length: 256 },
      false,
      ["encrypt", "decrypt"]
    );

    return [key, salt];
  }

  static async encryptFile(
    file: File,
    key: CryptoKey
  ): Promise<{ encryptedFile: Blob; iv: Uint8Array }> {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const fileBuffer = await file.arrayBuffer();

    const encryptedContent = await crypto.subtle.encrypt(
      {
        name: "AES-GCM",
        iv,
      },
      key,
      fileBuffer
    );

    return {
      encryptedFile: new Blob([encryptedContent]),
      iv,
    };
  }

  static async decryptFile(
    encryptedBlob: Blob,
    key: CryptoKey,
    iv: Uint8Array,
    originalFileName: string
  ): Promise<File> {
    const encryptedBuffer = await encryptedBlob.arrayBuffer();

    const decryptedContent = await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv,
      },
      key,
      encryptedBuffer
    );

    return new File([decryptedContent], originalFileName, {
      type: "application/octet-stream",
    });
  }
}

class FileService {
  async uploadFile(file: File, password: string) {
    const [key, salt] = await FileEncryption.generateKey(password);
    const { encryptedFile, iv } = await FileEncryption.encryptFile(file, key);

    const formData = new FormData();
    formData.append("file", encryptedFile, file.name);
    formData.append("iv", new Blob([iv]));
    formData.append("salt", new Blob([salt]));

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

  async downloadFile(fileId: number, password: string, fileName: string) {
    const response = await axiosInstance.get(`/files/download/${fileId}`, {
      responseType: "blob",
    });

    const base64ToArrayBuffer = (base64: string) => {
      const cleanBase64 = base64.replace(/[^A-Za-z0-9+/]/g, "");
      const paddedBase64 = cleanBase64.padEnd(
        cleanBase64.length + ((4 - (cleanBase64.length % 4)) % 4),
        "="
      );

      const binaryString = atob(paddedBase64);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      return bytes;
    };

    const iv = base64ToArrayBuffer(response.headers["x-iv"]);
    const salt = base64ToArrayBuffer(response.headers["x-salt"]);

    const [key] = await FileEncryption.generateKey(password, salt);

    const decryptedFile = await FileEncryption.decryptFile(
      response.data,
      key,
      iv,
      fileName
    );
    return decryptedFile;
  }

  async shareFile(shareDetails: FileShareRequest) {
    const response = await axiosInstance.post("/files/share", shareDetails);
    return response.data;
  }

  async deleteFile(fileId: number) {
    const response = await axiosInstance.delete(`/files/delete/${fileId}`);
    return response.data;
  }

  async accessSharedFile(token: string, password: string): Promise<File> {
    const response = await axiosInstance.get(
      `/files/shared/${token}?password=${password}`,
      {
        responseType: "blob",
      }
    );

    const base64ToArrayBuffer = (base64: string) => {
      const cleanBase64 = base64.replace(/[^A-Za-z0-9+/]/g, "");
      const paddedBase64 = cleanBase64.padEnd(
        cleanBase64.length + ((4 - (cleanBase64.length % 4)) % 4),
        "="
      );

      const binaryString = atob(paddedBase64);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      return bytes;
    };

    const iv = base64ToArrayBuffer(response.headers["x-iv"]);
    const salt = base64ToArrayBuffer(response.headers["x-salt"]);
    const fileName =
      response.headers["content-disposition"]
        ?.split("filename=")[1]
        ?.replace(/"/g, "") || "shared-file";

    const [key] = await FileEncryption.generateKey(password, salt);
    const decryptedFile = await FileEncryption.decryptFile(
      response.data,
      key,
      iv,
      fileName
    );
    return decryptedFile;
  }
}

export const fileService = new FileService();
