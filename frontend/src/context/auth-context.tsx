'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { authService, UserProfile } from '@/services/auth.service';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (full_name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();
  const queryClient = useQueryClient();

  const loadUser = useCallback(async () => {
    const storedToken = authService.getToken();
    if (!storedToken) {
      setToken(null);
      setUser(null);
      setIsLoading(false);
      return;
    }

    setToken(storedToken);
    try {
      const resp = await authService.getMe();
      if (resp.success && resp.data) {
        setUser(resp.data);
      } else {
        authService.logout();
        setUser(null);
        setToken(null);
      }
    } catch {
      authService.logout();
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const resp = await authService.login(email, password);
      if (resp.success && resp.data) {
        // Clear ALL cached query data from previous session before setting new user
        queryClient.clear();
        setUser(resp.data.user);
        setToken(resp.data.access_token);
        router.push('/upload');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (full_name: string, email: string, password: string) => {
    setIsLoading(true);
    try {
      const resp = await authService.signup(full_name, email, password);
      if (resp.success && resp.data) {
        // Clear ALL cached query data before new session
        queryClient.clear();
        setUser(resp.data.user);
        setToken(resp.data.access_token);
        router.push('/upload');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    // Clear ALL React Query cache — never show previous user's data
    queryClient.clear();
    setUser(null);
    setToken(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
