/**
 * Auth store using Zustand with persistence.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
}

interface AuthStore {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  // Actions
  setUser: (user: User) => void;
  setLoading: (loading: boolean) => void;
  clearUser: () => void;
  logout: () => void;
}

/**
 * Auth store with localStorage persistence.
 * Persists user data across page reloads but not tokens (kept in httpOnly cookies).
 */
export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      isLoading: true,
      isAuthenticated: false,

      setUser: (user: User) =>
        set({
          user,
          isAuthenticated: true,
          isLoading: false,
        }),

      setLoading: (loading: boolean) =>
        set({
          isLoading: loading,
        }),

      clearUser: () =>
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        }),

      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        }),
    }),
    {
      name: "auth-store", // localStorage key
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
