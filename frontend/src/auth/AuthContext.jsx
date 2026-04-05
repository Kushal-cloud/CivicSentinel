import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { client, setAuthToken } from "../api/client.js";

const AuthContext = createContext(null);

function decodeJwt(token) {
  try {
    const [, payload] = token.split(".");
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized + "===".slice((normalized.length + 3) % 4);
    const decoded = JSON.parse(atob(padded));
    return decoded;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("cs_token") || "");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const t = token || "";
    if (t) setAuthToken(t);
    else setAuthToken(null);
  }, [token]);

  const refreshMe = async () => {
    setLoading(true);
    try {
      const res = await client.get("/api/auth/me");
      setUser(res.data);
    } catch (err) {
      // Only clear token if the server explicitly rejects it (401 = invalid/expired)
      // Do NOT clear on network errors or 5xx — that would log the user out unfairly
      if (err?.response?.status === 401) {
        console.warn("Token rejected by server, signing out.");
        localStorage.removeItem("cs_token");
        setToken("");
        setUser(null);
      } else {
        console.error("Failed to refresh user (non-auth error):", err);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) refreshMe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const signIn = async ({ email, password }) => {
    setLoading(true);
    try {
      const res = await client.post("/api/auth/login", { email, password });
      const newToken = res.data.access_token;
      localStorage.setItem("cs_token", newToken);
      // Set the auth header immediately so /api/auth/me succeeds right away
      setAuthToken(newToken);
      setToken(newToken);
      // Fetch the user profile — errors here should propagate so Login.jsx can show them
      const meRes = await client.get("/api/auth/me");
      setUser(meRes.data);
      return res.data;
    } catch (err) {
      // On any login failure, clean up
      localStorage.removeItem("cs_token");
      setToken("");
      setUser(null);
      setAuthToken(null);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async ({ email, password, name, phone }) => {
    setLoading(true);
    try {
      await client.post("/api/auth/register", { email, password, name, phone });
      return true;
    } finally {
      setLoading(false);
    }
  };

  const signOut = () => {
    localStorage.removeItem("cs_token");
    setToken("");
    setUser(null);
  };

  const auth = useMemo(() => {
    const payload = token ? decodeJwt(token) : null;
    const role = payload?.role || user?.role || "citizen";
    return { token, user, role, loading, signIn, register, signOut, refreshMe };
  }, [token, user, loading]);

  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

