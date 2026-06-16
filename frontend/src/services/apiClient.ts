"""
API client with automatic token refresh, CSRF protection, and interceptors.
"""

import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,  // Include cookies in requests
});

// Track if we're currently refreshing the token
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(null);
    }
  });
  failedQueue = [];
};

// Request interceptor: Add token and CSRF token to requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Dynamically get access token from cookie
    const token = Cookies.get("access_token");
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add CSRF token for non-safe methods
    if (["POST", "PUT", "DELETE", "PATCH"].includes(config.method?.toUpperCase() || "")) {
      const csrfToken = Cookies.get("csrf_token");
      if (csrfToken) {
        config.headers["X-CSRF-Token"] = csrfToken;
      }
    }
    
    // Add request ID if available
    const requestId = sessionStorage.getItem("request_id");
    if (requestId) {
      config.headers["X-Request-ID"] = requestId;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle token expiration, CSRF errors, and retry
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Store request ID from response
    const requestId = response.headers["x-request-id"];
    if (requestId) {
      sessionStorage.setItem("request_id", requestId);
    }
    
    // Extract CSRF token from response if present and update cookie
    const csrfToken = response.headers["x-csrf-token"];
    if (csrfToken) {
      Cookies.set("csrf_token", csrfToken, {
        expires: 1,
        secure: process.env.NODE_ENV === "production",
        sameSite: "strict",
      });
    }
    
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    // Handle 403 Forbidden (CSRF token invalid or account deactivated)
    if (error.response?.status === 403) {
      const detail = (error.response?.data as any)?.detail || "";
      
      if (detail.includes("CSRF")) {
        // CSRF token invalid - refresh it
        try {
          const authService = require("./authService").default;
          await authService.login(
            (window as any).__lastEmail,
            (window as any).__lastPassword
          );
          return apiClient(originalRequest);
        } catch {
          const authService = require("./authService").default;
          authService.clearTokens();
          if (typeof window !== "undefined") {
            window.location.href = "/login";
          }
        }
      } else {
        // Account deactivated
        const authService = require("./authService").default;
        authService.clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }

    // Handle 401 Unauthorized (token expired, need refresh)
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue request if already refreshing
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => {
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Attempt to refresh token
        const authService = require("./authService").default;
        const refreshToken = authService.getRefreshToken();

        if (!refreshToken) {
          throw new Error("No refresh token available");
        }

        await authService.refreshAccessToken();
        processQueue();

        // Retry original request with new token
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);

        // Clear tokens and redirect to login
        const authService = require("./authService").default;
        authService.clearTokens();

        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Handle 429 Too Many Requests (rate limited)
    if (error.response?.status === 429) {
      const detail = (error.response?.data as any)?.detail || "Too many requests";
      const retryAfter = error.response?.headers["retry-after"];
      console.warn(`Rate limited: ${detail}. Retry after: ${retryAfter}s`);
    }

    return Promise.reject(error);
  }
);

export default apiClient;

