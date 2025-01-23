export interface UserCreate {
    username: string;
    email: string;
    password: string;
    role?: string;
    mfa_enabled?: boolean;
}

export interface UserLogin {
    username: string;
    password: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: {
        username: string;
        email: string;
        role: string;
    };
    message?: string;
    require_mfa?: boolean;
}
