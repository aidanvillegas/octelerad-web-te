"use client";

import axios from "axios";
import toast from "react-hot-toast";

export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const http = axios.create({
  baseURL: API,
  withCredentials: false,
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "Network error";
    toast.error(String(message));
    return Promise.reject(error);
  }
);
