import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

const ShieldIcon = () => (
  <svg viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 2L17 5.5V11C17 14.5 13.5 17.5 10 19C6.5 17.5 3 14.5 3 11V5.5L10 2Z"
      fill="rgba(255,255,255,0.9)" />
    <circle cx="10" cy="11" r="3" fill="#7c3aed" />
  </svg>
);

export default function TopNav() {
  const nav = useNavigate();
  const loc = useLocation();
  const { signOut, user, role } = useAuth();

  const onLogout = () => {
    signOut();
    nav("/login", { replace: true });
  };

  const initials = user?.name
    ? user.name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() || "U";

  const [theme, setTheme] = React.useState(
    () => document.documentElement.getAttribute("data-theme") || "light"
  );

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
  };

  return (
    <nav className="topnav">
      <div className="topnav-left">
        <div className="topnav-logo">
          <ShieldIcon />
        </div>
        <span className="topnav-brand" style={{ marginRight: 20 }}>CivicSentinel</span>
        <span className="topnav-role" style={{ marginRight: 20 }}>{role?.toUpperCase() || "CITIZEN"}</span>

        <div className="topnav-links" style={{ display: "flex", gap: "10px" }}>
            <button
              className={`topnav-btn${loc.pathname === "/" ? " active" : ""}`}
              onClick={() => nav("/", { replace: true })}
            >
              📝 Report Issue
            </button>
            <button
              className={`topnav-btn${loc.pathname === "/gallery" ? " active" : ""}`}
              onClick={() => nav("/gallery", { replace: true })}
            >
              📸 Success Gallery
            </button>
            <button
              className={`topnav-btn${loc.pathname === "/my-complaints" ? " active" : ""}`}
              onClick={() => nav("/my-complaints", { replace: true })}
            >
              📋 My Complaints
            </button>
        </div>
      </div>

      <div className="topnav-right">
        <button
          className={`topnav-btn${loc.pathname === "/profile" ? " active" : ""}`}
          type="button"
          onClick={() => nav("/profile")}
          title="User Profile"
        >
          👤 Profile
        </button>

        <button
          className="topnav-btn"
          type="button"
          onClick={toggleTheme}
          title="Toggle Theme"
          style={{ padding: "7px 10px", fontSize: "16px" }}
        >
          {theme === "light" ? "🌙" : "☀️"}
        </button>

        {role === "admin" && (
          <button
            className={`topnav-btn${loc.pathname === "/admin" ? " active" : ""}`}
            type="button"
            onClick={() => nav("/admin", { replace: true })}
            id="nav-admin-btn"
          >
            🛡️ Admin Dashboard
          </button>
        )}

        <div className="topnav-avatar" title={user?.email}>{initials}</div>

        <button
          className="topnav-logout"
          type="button"
          onClick={onLogout}
          id="nav-logout-btn"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
