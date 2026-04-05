import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

const FEATURES = [
  { icon: "🎯", title: "Vision Detection", desc: "AI identifies civil issues from photos with multi-class labels and severity estimation." },
  { icon: "🗺️", title: "Location & Authority", desc: "Maps each report to the right municipal department based on GPS or address." },
  { icon: "✍️", title: "AI Complaint Letter", desc: "Generates a formal letter in 11 Indian languages with tone customization." },
  { icon: "📊", title: "Live Tracking", desc: "Real-time status updates and analytics for citizens and administrators." },
];

export default function LoginPage() {
  const nav = useNavigate();
  const { signIn, register, user } = useAuth();

  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [err, setErr] = useState("");
  const [submitting, setSubmitting] = useState(false);

  React.useEffect(() => {
    if (user) nav("/", { replace: true });
  }, [user, nav]);

  const friendlyError = (ex) => {
    const detail = ex?.response?.data?.detail;
    const status = ex?.response?.status;
    const msg = ex?.message || "";
    if (!detail && msg.toLowerCase().includes("network")) return "Network error — is the backend running?";
    if (Array.isArray(detail)) return detail.map(e => { const f = Array.isArray(e.loc) ? e.loc.slice(1).join(".") : ""; return f ? `${f}: ${e.msg}` : e.msg; }).join(" · ");
    if (typeof detail === "string") return detail;
    if (status === 409) return "Email already registered. Try logging in instead.";
    if (status === 401) return "Invalid email or password.";
    if (status === 500) return "Server error — please try again.";
    return msg || "Something went wrong. Please try again.";
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      setSubmitting(true);
      if (mode === "login") {
        await signIn({ email, password });
      } else {
        await register({ email, password, name, phone: phone || null });
        await signIn({ email, password });
      }
    } catch (ex) {
      setErr(friendlyError(ex));
    } finally {
      setSubmitting(false);
    }
  };

  const busy = submitting;

  return (
    <div className="auth-page">
      <div className="auth-grid">
        {/* Left panel */}
        <div className="glass auth-left">
          <div className="brand">
            <div className="brand-mark">🛡️</div>
            <div>
              <h1 className="brand-title">CivicSentinel</h1>
              <div className="brand-subtitle">AI-powered civic intelligence</div>
            </div>
          </div>

          <div className="feature-list">
            {FEATURES.map((f, i) => (
              <div className="feature-item" key={i}>
                <div className="feature-icon">{f.icon}</div>
                <div className="feature-text">
                  <strong>{f.title}</strong>
                  <span>{f.desc}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="muted" style={{ marginTop: "auto", paddingTop: 24, fontSize: 12 }}>
            Futuristic Smart City Portal · MVP
          </div>
        </div>

        {/* Right panel */}
        <div className="glass auth-right">
          <h2 className="auth-card-title">
            {mode === "login" ? "Welcome back" : "Create account"}
          </h2>
          <div className="muted">
            {mode === "login" ? "Sign in to report and track civic issues." : "Join to submit and track civic issues."}
          </div>

          <div className="auth-tabs">
            <button id="tab-login" className={`auth-tab${mode === "login" ? " auth-tab-active" : ""}`} type="button" onClick={() => { setMode("login"); setErr(""); }} disabled={busy}>Sign In</button>
            <button id="tab-register" className={`auth-tab${mode === "register" ? " auth-tab-active" : ""}`} type="button" onClick={() => { setMode("register"); setErr(""); }} disabled={busy}>Register</button>
          </div>

          <form onSubmit={onSubmit} className="form" id="auth-form">
            {mode === "register" && (
              <>
                <label htmlFor="auth-name">Full Name</label>
                <input id="auth-name" value={name} onChange={e => setName(e.target.value)} placeholder="Raj Kumar" required autoComplete="name" />
              </>
            )}

            <label htmlFor="auth-email">Email Address</label>
            <input id="auth-email" value={email} onChange={e => setEmail(e.target.value)} type="email" placeholder="you@example.com" required autoComplete="email" />

            <label htmlFor="auth-password">Password</label>
            <input id="auth-password" value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="••••••••" required autoComplete={mode === "login" ? "current-password" : "new-password"} />

            {mode === "register" && (
              <>
                <label htmlFor="auth-phone">Phone <span className="muted">(optional)</span></label>
                <input id="auth-phone" value={phone} onChange={e => setPhone(e.target.value)} type="tel" placeholder="+91 98765 43210" autoComplete="tel" />
              </>
            )}

            {err && <div className="error">{err}</div>}

            <button className="primary" id="auth-submit-btn" disabled={busy}>
              {busy ? <><span className="spinner" /> Please wait…</> : mode === "login" ? "Sign In →" : "Create Account →"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
