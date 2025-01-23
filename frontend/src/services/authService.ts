import { UserCreate, UserLogin, AuthResponse } from "../types/auth";
import { axiosInstance } from "../config/axios";

export const authService = {
  async register(userData: UserCreate): Promise<AuthResponse> {
    const { data } = await axiosInstance.post("/auth/register", userData);
    return data;
  },

  async login(credentials: UserLogin): Promise<AuthResponse> {
    const { data } = await axiosInstance.post("/auth/login", credentials);
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
};
