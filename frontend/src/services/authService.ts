import {
  UserCreate,
  UserLogin,
  AuthResponse,
  LoginResponse,
  MFAVerify,
} from "../types/auth";
import { axiosInstance } from "../config/axios";

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  created_at: string;
}

export const authService = {
  async register(userData: UserCreate): Promise<AuthResponse> {
    const { data } = await axiosInstance.post("/auth/register", userData);
    return data;
  },

  async login(credentials: UserLogin): Promise<LoginResponse> {
    const { data } = await axiosInstance.post("/auth/login", credentials);
    return data;
  },

  async verifyMFA(verifyData: MFAVerify): Promise<AuthResponse> {
    const { data } = await axiosInstance.post("/auth/verify-mfa", verifyData);
    return data;
  },

  async validateToken(): Promise<boolean> {
    try {
      await axiosInstance.get("/auth/validate-token");
      return true;
    } catch {
      return false;
    }
  },

  async toggleMFA(): Promise<{ mfa_enabled: boolean }> {
    const { data } = await axiosInstance.post("/auth/toggle-mfa");
    return data;
  },

  async listUsers(): Promise<{ users: User[] }> {
    const { data } = await axiosInstance.get("/auth/users");
    return data;
  },

  async updateUserRole(userId: number, newRole: string): Promise<void> {
    await axiosInstance.put(`/auth/users/${userId}/role`, {
      new_role: newRole,
    });
  },

  async deleteAccount(): Promise<void> {
    await axiosInstance.delete("/auth/account");
  },
};
