import React, { useState } from "react";
import { useAuth } from "../auth/AuthContext.jsx";
import { client } from "../api/client.js";

export default function Profile() {
  const { user, refreshMe } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [phone, setPhone] = useState(user?.phone || "");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const initials = (user?.name || user?.email || "U")
    .split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();

  const handleSave = async (e) => {
    e.preventDefault();
    setMsg(""); setErr(""); setBusy(true);
    try {
      await client.put("/api/auth/me", { name, phone });
      await refreshMe();
      setMsg("✅ Profile updated successfully!");
    } catch (ex) {
      setErr(ex?.response?.data?.detail || ex.message || "Update failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container fade-up" style={{ maxWidth: 680 }}>
      <div className="page-header" style={{ marginBottom: 28 }}>
        <h2 className="page-title">👤 My Profile</h2>
        <div className="muted">Manage your account details</div>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 24 }}>
          <div style={{
            width: 72, height: 72, borderRadius: "50%",
            background: "linear-gradient(135deg, #7c3aed, #5b21b6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 26, fontWeight: 800, color: "#fff",
            boxShadow: "0 0 0 4px rgba(124,58,237,0.2)"
          }}>{initials}</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>{user?.name || "—"}</div>
            <div className="muted" style={{ fontSize: 13 }}>{user?.email}</div>
            <span className="badge badge-violet" style={{ marginTop: 6 }}>{user?.role?.toUpperCase() || "CITIZEN"}</span>
          </div>
        </div>
        <div className="divider" />
        <form onSubmit={handleSave} className="form" style={{ marginTop: 16 }}>
          <label>Full Name</label>
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Your full name" />
          <label>Phone Number</label>
          <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="+91 XXXXX XXXXX" />
          <label style={{ marginTop: 8 }}>Email Address <span className="muted">(cannot be changed)</span></label>
          <input value={user?.email || ""} disabled style={{ opacity: 0.6 }} />
          {msg && <div className="notice" style={{ color: "var(--success)", background: "rgba(16,185,129,0.1)", borderColor: "rgba(16,185,129,0.3)", marginTop: 12 }}>{msg}</div>}
          {err && <div className="error" style={{ marginTop: 12 }}>{err}</div>}
          <button className="primary" disabled={busy} style={{ maxWidth: 200, marginTop: 16 }}>
            {busy ? <><span className="spinner" /> Saving…</> : "💾 Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}
