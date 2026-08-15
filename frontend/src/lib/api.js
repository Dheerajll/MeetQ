// src/lib/api.js

import axios from "axios";

// Same-origin path, rewritten to the real backend in next.config.mjs — keeps
// the refresh_token cookie scoped to this origin instead of a cross-origin one.
const API_URL = "/api";

let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // required — browser sends httpOnly refresh_token cookie automatically
});

// Attach access token to every outgoing request
api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// 401 → try refresh once → retry original request
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    // The refresh call itself must never trigger another refresh attempt —
    // otherwise a failed refresh recurses into itself and forces a reload loop.
    const isRefreshCall = originalRequest?.url?.includes("/auth/refresh");

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isRefreshCall
    ) {
      originalRequest._retry = true;

      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post(
              "/api/auth/refresh",
              {}, // no body — backend reads httpOnly cookie automatically
              { withCredentials: true }
            )
            .then((res) => res.data)
            .finally(() => {
              refreshPromise = null;
            });
        }

        const data = await refreshPromise;
        setAccessToken(data.access_token); // snake_case — matches backend

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        setAccessToken(null);
        if (typeof window !== "undefined" && window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;