import {
  UserCreate,
  UserLogin,
  AuthResponse,
  LoginResponse,
  MFAVerify,
} from "../types/auth";
import { axiosInstance } from "../config/axios";

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
};
