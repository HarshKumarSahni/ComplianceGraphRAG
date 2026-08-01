import apiClient from '@/lib/api-client';
import { ApiResponse } from '@/types/api';

export interface UserProfile {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokenData {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

const TOKEN_KEY = 'graphguard_auth_token';

export const authService = {
  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEY);
    }
    return null;
  },

  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEY, token);
    }
  },

  removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
    }
  },

  async signup(full_name: string, email: string, password: string): Promise<ApiResponse<AuthTokenData>> {
    const response = await apiClient.post<ApiResponse<AuthTokenData>>('/auth/signup', {
      full_name,
      email,
      password,
    });
    if (response.data?.data?.access_token) {
      this.setToken(response.data.data.access_token);
    }
    return response.data;
  },

  async login(email: string, password: string): Promise<ApiResponse<AuthTokenData>> {
    const response = await apiClient.post<ApiResponse<AuthTokenData>>('/auth/login', {
      email,
      password,
    });
    if (response.data?.data?.access_token) {
      this.setToken(response.data.data.access_token);
    }
    return response.data;
  },

  async getMe(): Promise<ApiResponse<UserProfile>> {
    const response = await apiClient.get<ApiResponse<UserProfile>>('/auth/me');
    return response.data;
  },

  logout(): void {
    this.removeToken();
  },
};
