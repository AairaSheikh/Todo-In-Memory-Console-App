/**Authentication context and hooks for managing user session.*/

'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { authAPI } from './api';

interface AuthContextType {
  userId: string | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (userId: string, token: string) => void;
  logout: () => void;
  refreshSession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load auth from localStorage on mount
  useEffect(() => {
    const loadAuth = () => {
      if (typeof window !== 'undefined') {
        const storedUserId = localStorage.getItem('user_id');
        const storedToken = localStorage.getItem('token');
        
        console.log('Loading auth from localStorage:', { storedUserId, storedToken });
        
        if (storedUserId && storedToken) {
          setUserId(storedUserId);
          setToken(storedToken);
        }
      }
      setIsLoading(false);
    };

    loadAuth();
  }, []);

  const login = useCallback((newUserId: string, newToken: string) => {
    console.log('AuthProvider.login called with:', { newUserId, newToken });
    
    if (typeof window !== 'undefined') {
      console.log('Setting localStorage - user_id:', newUserId, 'token:', newToken);
      localStorage.setItem('user_id', newUserId);
      localStorage.setItem('token', newToken);
      console.log('localStorage after set:', {
        user_id: localStorage.getItem('user_id'),
        token: localStorage.getItem('token')
      });
    }
    
    setUserId(newUserId);
    setToken(newToken);
    console.log('Auth state updated:', { userId: newUserId, token: newToken });
  }, []);

  const logout = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user_id');
      localStorage.removeItem('token');
    }
    setUserId(null);
    setToken(null);
  }, []);

  const refreshSession = async (): Promise<boolean> => {
    if (!token) return false;

    try {
      const response = await authAPI.getCurrentUser();
      return !!response.data;
    } catch (error) {
      logout();
      return false;
    }
  };

  const isAuthenticated = !!userId && !!token;

  console.log('AuthProvider rendering with:', { userId, token, isAuthenticated, isLoading });

  const value: AuthContextType = {
    userId,
    token,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function useToken() {
  const { token } = useAuth();
  return token;
}
