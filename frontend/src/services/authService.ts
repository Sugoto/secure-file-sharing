import { UserCreate, UserLogin, AuthResponse } from '../types/auth';
import { httpClient } from './httpClient';

export const authService = {
    async register(userData: UserCreate): Promise<AuthResponse> {
        return httpClient.post('/auth/register', userData);
    },

    async login(credentials: UserLogin): Promise<AuthResponse> {
        return httpClient.post('/auth/login', credentials);
    },

    async validateToken(): Promise<boolean> {
        try {
            await httpClient.get('/auth/validate-token');
            return true;
        } catch {
            return false;
        }
    }
};
