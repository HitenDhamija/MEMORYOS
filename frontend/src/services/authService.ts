/**
 * Authentication service with token management, CSRF protection, and security best practices.
 */

import apiClient from "./apiClient";
import Cookies from "js-cookie";

interface LoginPayload {
  email: string;
  password: string;
}

interface RegisterPayload extends LoginPayload {
  username: string;
  full_name?: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

interface UserProfile {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface UpdateProfilePayload {
  email?: string;
  full_name?: string;
  password?: string;
}

const TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const CSRF_TOKEN_KEY = "csrf_token";

const authService = {
  /**
   * Register a new user
   */
  async register(data: RegisterPayload): Promise<UserProfile> {
    try {
      const response = await apiClient.post<UserProfile>("/v1/auth/register", data);
      // Extract CSRF token if returned
      this._extractAndStoreCsrfToken(response);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  /**
   * Login with email and password
   * Stores credentials temporarily for CSRF token refresh if needed
   */
  async login(credentials: LoginPayload): Promise<TokenResponse> {
    try {
      // Store credentials temporarily (cleared on logout)
      (window as any).__lastEmail = credentials.email;
      (window as any).__lastPassword = credentials.password;
      
      const response = await apiClient.post<TokenResponse>("/v1/auth/login", credentials);
      const { access_token, refresh_token } = response.data;

      this.setTokens(access_token, refresh_token);
      // Extract CSRF token if returned
      this._extractAndStoreCsrfToken(response);
      
      return response.data;
    } catch (error) {
      // Clear stored credentials on error
      delete (window as any).__lastEmail;
      delete (window as any).__lastPassword;
      throw error;
    }
  },

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken(): Promise<AccessTokenResponse> {
    const refreshToken = this.getRefreshToken();

    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await apiClient.post<AccessTokenResponse>("/v1/auth/refresh", {
        refresh_token: refreshToken,
      });

      const { access_token } = response.data;
      this.setAccessToken(access_token);
      // Extract CSRF token if returned
      this._extractAndStoreCsrfToken(response);

      return response.data;
    } catch (error) {
      // Refresh token invalid or expired, clear all tokens
      this.clearTokens();
      throw error;
    }
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post("/v1/auth/logout");
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn("Logout API call failed:", error);
    } finally {
      this.clearTokens();
      // Clear stored credentials
      delete (window as any).__lastEmail;
      delete (window as any).__lastPassword;
    }
  },

  /**
   * Get current user profile
   */
  async getProfile(): Promise<UserProfile> {
    const response = await apiClient.get<UserProfile>("/v1/users/me");
    return response.data;
  },

  /**
   * Update user profile
   */
  async updateProfile(data: UpdateProfilePayload): Promise<UserProfile> {
    const response = await apiClient.put<UserProfile>("/v1/users/me", data);
    return response.data;
  },

  /**
   * Upload avatar image
   */
  async uploadAvatar(file: File): Promise<UserProfile> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post<UserProfile>("/v1/users/me/avatar", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  /**
   * Deactivate account
   */
  async deactivateAccount(): Promise<void> {
    await apiClient.post("/v1/users/me/deactivate");
    this.clearTokens();
  },

  /**
   * Set both tokens in secure cookies
   */
  setTokens(accessToken: string, refreshToken: string): void {
    Cookies.set(TOKEN_KEY, accessToken, {
      expires: 1, // 1 day (access token shorter lived)
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
    });

    Cookies.set(REFRESH_TOKEN_KEY, refreshToken, {
      expires: 7, // 7 days
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
    });
  },

  /**
   * Set access token only
   */
  setAccessToken(token: string): void {
    Cookies.set(TOKEN_KEY, token, {
      expires: 1,
      secure: process.env.NODE_ENV === "production",
      sameSite: "strict",
      path: "/",
    });
  },

  /**
   * Get access token
   */
  getAccessToken(): string | undefined {
    return Cookies.get(TOKEN_KEY);
  },

  /**
   * Get refresh token
   */
  getRefreshToken(): string | undefined {
    return Cookies.get(REFRESH_TOKEN_KEY);
  },

  /**
   * Get CSRF token
   */
  getCsrfToken(): string | undefined {
    return Cookies.get(CSRF_TOKEN_KEY);
  },

  /**
   * Clear both tokens and CSRF token
   */
  clearTokens(): void {
    Cookies.remove(TOKEN_KEY, { path: "/" });
    Cookies.remove(REFRESH_TOKEN_KEY, { path: "/" });
    Cookies.remove(CSRF_TOKEN_KEY, { path: "/" });
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  },

  /**
   * Check if refresh token exists
   */
  hasRefreshToken(): boolean {
    return !!this.getRefreshToken();
  },

  /**
   * Extract and store CSRF token from response
   */
  _extractAndStoreCsrfToken(response: any): void {
    const csrfToken = response.headers["x-csrf-token"];
    if (csrfToken) {
      Cookies.set(CSRF_TOKEN_KEY, csrfToken, {
        expires: 1,
        secure: process.env.NODE_ENV === "production",
        sameSite: "strict",
        path: "/",
        // Note: httponly=false because we need to read it
      });
    }
  },
};

export default authService;
export type {
  TokenResponse,
  AccessTokenResponse,
  UserProfile,
  UpdateProfilePayload,
  LoginPayload,
  RegisterPayload,
};

