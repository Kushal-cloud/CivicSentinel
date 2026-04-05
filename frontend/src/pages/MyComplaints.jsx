import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { client } from "../api/client.js";

const STATUS_COLORS = {
  received: "badge-info",
  review_pending: "badge-warning",
  ready_for_submission: "badge-violet",
  submitted: "badge-violet",
  in_progress: "badge-info",
  resolved: "badge-success",
  escalated: "badge-danger",
  rejected: "badge-danger",
  flagged: "badge-danger",
};

export default function MyComplaints() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const res = await client.get("/api/complaints/my");
        setComplaints(res.data || []);
      } catch (e) {
        setErr(e?.response?.data?.detail || e.message || "Failed to load complaints.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return (
    <div className="container" style={{ padding: "40px" }}>
      <div className="spinner" /> Loading your complaints…
    </div>
  );

  return (
    <div className="container fade-up">
      <div className="page-header" style={{ marginBottom: 28 }}>
        <h2 className="page-title">📋 My Complaints</h2>
        <div className="muted">All issues you have reported through CivicSentinel</div>
      </div>

      {err && <div className="error" style={{ marginBottom: 16 }}>{err}</div>}

      {complaints.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "60px 20px" }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📭</div>
          <h4>No complaints yet!</h4>
          <div className="muted" style={{ marginBottom: 16 }}>You haven't reported any civic issues yet.</div>
          <button className="btn btn-primary" onClick={() => nav("/")}>+ Report Your First Issue</button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {complaints.map(c => (
            <div
              key={c.tracking_id}
              className="card"
              style={{ cursor: "pointer", transition: "border-color 0.2s" }}
              onClick={() => nav(`/complaints/${c.tracking_id}`)}
              onMouseEnter={e => e.currentTarget.style.borderColor = "var(--primary)"}
              onMouseLeave={e => e.currentTarget.style.borderColor = ""}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                    <code style={{ fontSize: 13, color: "var(--primary-light)", fontWeight: 700 }}>{c.tracking_id}</code>
                    <span className={`badge ${STATUS_COLORS[c.status] || "badge-muted"}`}>
                      {(c.status || "").replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    {c.fraud_flag && <span className="badge badge-danger">⚠️ Flagged</span>}
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>
                    {(c.issue_category || "Unknown Issue").replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div className="muted small">📍 {[c.locality, c.ward].filter(Boolean).join(", ") || "Location not specified"}</div>
                </div>
                <div style={{ textAlign: "right", flexShrink: 0 }}>
                  <div className="muted small">{c.created_at ? new Date(c.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "—"}</div>
                  <div style={{ marginTop: 6, display: "flex", gap: 8, justifyContent: "flex-end" }}>
                    <span className="muted small">👍 {c.upvotes || 0}</span>
                    <span className="muted small">🔄 {c.follow_up_count || 0} follow-ups</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
