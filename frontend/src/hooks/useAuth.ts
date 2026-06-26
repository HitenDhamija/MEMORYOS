/**
 * Authentication hook with session management.
 */

import { useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import authService, { type UpdateProfilePayload } from "@/services/authService";
import { useAuthStore } from "@/context/authStore";

interface UseAuthReturn {
  user: any;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: UpdateProfilePayload) => Promise<void>;
  deactivateAccount: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

export const useAuth = (): UseAuthReturn => {
  const router = useRouter();
  const { user, isAuthenticated, setUser, clearUser, setLoading, isLoading } = useAuthStore();

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if user has valid tokens
        if (authService.isAuthenticated()) {
          // Attempt to fetch current user profile
          const profile = await authService.getProfile();
          setUser(profile as any);
        } else if (authService.hasRefreshToken()) {
          // Try to refresh if refresh token exists
          try {
            await authService.refreshAccessToken();
            const profile = await authService.getProfile();
            setUser(profile as any);
          } catch (error) {
            // Refresh failed, clear tokens
            authService.clearTokens();
            clearUser();
          }
        } else {
          clearUser();
        }
      } catch (error) {
        console.error("Auth initialization failed:", error);
        clearUser();
      }
    };

    initializeAuth();
  }, [setUser, clearUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      try {
        await authService.login({ email, password });
        const profile = await authService.getProfile();
        setUser(profile as any);
        router.push("/dashboard");
      } catch (error: any) {
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [setUser, setLoading, router]
  );

  const register = useCallback(
    async (email: string, username: string, password: string, fullName?: string) => {
      setLoading(true);
      try {
        await authService.register({ email, username, password, full_name: fullName });
        router.push("/login");
      } catch (error: any) {
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, router]
  );

  const logout = useCallback(async () => {
    try {
      await authService.logout();
      clearUser();
      router.push("/login");
    } catch (error: any) {
      console.error("Logout error:", error);
      // Still clear local state even if API call fails
      clearUser();
      router.push("/login");
    }
  }, [clearUser, router]);

  const updateProfile = useCallback(
    async (data: UpdateProfilePayload) => {
      try {
        const updated = await authService.updateProfile(data);
        setUser(updated as any);
      } catch (error: any) {
        throw error;
      }
    },
    [setUser]
  );

  const deactivateAccount = useCallback(async () => {
    try {
      await authService.deactivateAccount();
      clearUser();
      router.push("/login");
    } catch (error) {
      console.error("Deactivation error:", error);
      throw error;
    }
  }, [clearUser, router]);

  const refreshSession = useCallback(async () => {
    try {
      await authService.refreshAccessToken();
    } catch (error) {
      console.error("Session refresh failed:", error);
      clearUser();
      router.push("/login");
    }
  }, [clearUser, router]);

  return {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
    deactivateAccount,
    refreshSession,
  };
};
