import axios from "axios";

// In dev: empty string → same-origin → Vite proxy forwards to backend (no CORS)
// In Docker prod: VITE_API_BASE_URL must be set to the publicly reachable backend URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export const client = axios.create({
  baseURL: API_BASE_URL,
});

export function setAuthToken(token) {
  if (token) {
    client.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete client.defaults.headers.common["Authorization"];
  }
}

