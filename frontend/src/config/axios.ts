import axios from 'axios';
import { useAuthStore } from '../store/authStore';

export const API_URL = 'http://localhost:8000';

export const axiosInstance = axios.create({
  baseURL: API_URL,
});

axiosInstance.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
