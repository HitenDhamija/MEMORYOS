"""
Auth provider component for global auth context and session management.
"""

"use client";

import React, { useEffect } from "react";
import authService from "@/services/authService";
import { useAuthStore } from "@/context/authStore";

interface AuthProviderProps {
  children: React.ReactNode;
}

/**
 * AuthProvider component that initializes auth state and manages session.
 * Should wrap the entire application for proper auth management.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const { setUser, clearUser, setLoading } = useAuthStore();

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if user has valid access token
        if (authService.isAuthenticated()) {
          try {
            const profile = await authService.getProfile();
            setUser(profile as any);
          } catch (error) {
            console.error("Failed to fetch profile:", error);
            clearUser();
          }
        } else if (authService.hasRefreshToken()) {
          // Try to refresh if we have a refresh token
          try {
            await authService.refreshAccessToken();
            const profile = await authService.getProfile();
            setUser(profile as any);
          } catch (error) {
            console.error("Token refresh failed:", error);
            authService.clearTokens();
            clearUser();
          }
        } else {
          clearUser();
        }
      } catch (error) {
        console.error("Auth initialization error:", error);
        clearUser();
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, [setUser, clearUser, setLoading]);

  return <>{children}</>;
}

export default AuthProvider;
