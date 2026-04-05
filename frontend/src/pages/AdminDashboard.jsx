import React, { useEffect, useMemo, useState } from "react";
import { client } from "../api/client.js";
import HeatmapMap from "../components/HeatmapMap.jsx";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const STATUS_OPTIONS = ["submitted", "in_progress", "resolved", "escalated", "rejected", "flagged"];

const CHART_COLORS = ["#7c3aed", "#10b981", "#f59e0b", "#3b82f6", "#ef4444", "#14b8a6", "#8b5cf6", "#f97316"];

function statusBadgeClass(s) {
  const map = { received: "badge status-received", review_pending: "badge status-review_pending", ready_for_submission: "badge status-ready_for_submission", submitted: "badge status-submitted", in_progress: "badge status-in_progress", resolved: "badge status-resolved", escalated: "badge status-escalated", rejected: "badge status-rejected", flagged: "badge status-flagged" };
  return map[s] || "badge badge-muted";
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--surface-3)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "var(--text)" }}>
      <div style={{ fontWeight: 700 }}>{label || payload[0]?.name}</div>
      <div style={{ color: "#c4b5fd" }}>{payload[0]?.value}</div>
    </div>
  );
};

export default function AdminDashboard() {
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [summary, setSummary] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [predictive, setPredictive] = useState(null);
  const [complaints, setComplaints] = useState([]);
  const [statusToSet, setStatusToSet] = useState({});
  const [deptToSet, setDeptToSet] = useState({});
  const [msgToSet, setMsgToSet] = useState({});

  const refresh = async () => {
    setErr(""); setLoading(true);
    try {
      const [s, h, p, list] = await Promise.all([
        client.get("/api/analytics/summary"),
        client.get("/api/analytics/heatmap"),
        client.get("/api/analytics/predictive"),
        client.get("/api/admin/complaints?limit=50&offset=0"),
      ]);
      setSummary(s.data); setHeatmap(h.data); setPredictive(p.data);
      setComplaints(list.data || []);
    } catch (ex) {
      setErr(ex?.response?.data?.detail || ex.message || "Failed to load dashboard");
    } finally { setLoading(false); }
  };

  useEffect(() => { refresh(); }, []);

  const issueChartData = useMemo(() => Object.entries(summary?.by_issue_category || {}).map(([k, v]) => ({ name: k.replace(/_/g, " "), value: v })), [summary]);
  const deptPieData = useMemo(() => Object.entries(summary?.by_department || {}).map(([k, v]) => ({ name: k, value: v })), [summary]);
  const statusCounts = useMemo(() => {
    const counts = {};
    (complaints || []).forEach(c => { counts[c.status] = (counts[c.status] || 0) + 1; });
    return counts;
  }, [complaints]);

  const onUpdateStatus = async (trackingId) => {
    const newStatus = statusToSet[trackingId] || "in_progress";
    const department_name = deptToSet[trackingId] || null;
    const message = msgToSet[trackingId] || null;
    try {
      await client.patch(`/api/admin/complaints/${trackingId}/status`, { status: newStatus, department_name, message });
      await refresh();
    } catch (ex) { setErr(ex?.response?.data?.detail || ex.message || "Update failed"); }
  };

  if (loading) return (
    <div className="container loading-screen">
      <div className="loading-spinner" />
      <div className="muted">Loading dashboard…</div>
    </div>
  );

  const total = summary?.total_complaints || 0;
  const resolved = summary?.by_status?.resolved || 0;
  const pending = (summary?.by_status?.review_pending || 0) + (summary?.by_status?.received || 0);
  const flagged = summary?.by_status?.flagged || 0;

  return (
    <div className="container fade-up">
      <div className="page-header">
        <h2 className="page-title">Admin Dashboard</h2>
        <div className="muted">Analytics, prioritization, and real-time complaint management</div>
      </div>

      {err && <div className="error">{err}</div>}

      {/* KPI Row */}
      <div className="grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: 20 }}>
        <div className="stat-card">
          <div className="stat-icon stat-icon-violet">📊</div>
          <div><div className="stat-value">{total}</div><div className="stat-label">Total Reports</div></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon stat-icon-success">✅</div>
          <div><div className="stat-value" style={{ color: "var(--success)" }}>{resolved}</div><div className="stat-label">Resolved</div></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon stat-icon-warning">⏳</div>
          <div><div className="stat-value" style={{ color: "var(--accent)" }}>{pending}</div><div className="stat-label">Pending Review</div></div>
        </div>
        <div className="stat-card">
          <div className="stat-icon stat-icon-danger">🚩</div>
          <div><div className="stat-value" style={{ color: "var(--danger)" }}>{flagged}</div><div className="stat-label">Flagged</div></div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>📈 Issue Frequency</div>
          <div className="muted small" style={{ marginBottom: 12 }}>By issue category</div>
          {issueChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={issueChartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} />
                <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="muted">No data yet.</div>}
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>🏢 Department Distribution</div>
          <div className="muted small" style={{ marginBottom: 12 }}>By mapped department</div>
          {deptPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={deptPieData} dataKey="value" nameKey="name" outerRadius={90} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                  {deptPieData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div className="muted">No data yet.</div>}
        </div>
      </div>

      {/* Heatmap + Predictive */}
      <div className="grid grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>🗺️ Location Heatmap</div>
          {heatmap?.cells ? <HeatmapMap cells={heatmap.cells} /> : <div className="muted">No coordinates reported yet.</div>}
        </div>

        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>⚠️ Predictive Risk Zones</div>
          {(predictive?.zones || []).length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {predictive.zones.map((z, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", background: "var(--hover-bg)", borderRadius: 8, border: "1px solid var(--border)" }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{z.ward || "Unknown Ward"}</div>
                    <div className="muted small">Recent: {z.recent_count} · Prev: {z.previous_count}</div>
                  </div>
                  <div className={`badge ${z.risk_score >= 0.7 ? "badge-danger" : z.risk_score >= 0.4 ? "badge-warning" : "badge-success"}`}>
                    Risk: {typeof z.risk_score === "number" ? z.risk_score.toFixed(2) : z.risk_score}
                  </div>
                </div>
              ))}
            </div>
          ) : <div className="muted">No risk zones computed yet.</div>}
        </div>
      </div>

      {/* Complaint Queue */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: 18 }}>📋 Complaint Queue</div>
        <div className="table-wrap">
          <table className="table" id="complaints-table">
            <thead>
              <tr>
                <th>Tracking ID</th>
                <th>Status</th>
                <th>Category</th>
                <th>Ward</th>
                <th>Severity</th>
                <th>Priority</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {complaints.map((c) => {
                const tid = c.tracking_id;
                return (
                  <tr key={tid}>
                    <td><a href={`/complaints/${tid}`} className="mono" style={{ color: "var(--primary-light)", fontSize: 13 }}>{tid}</a></td>
                    <td><span className={statusBadgeClass(c.status)}>{(c.status || "").replace(/_/g, " ")}</span></td>
                    <td style={{ fontSize: 13 }}>{(c.issue_category || "—").replace(/_/g, " ")}</td>
                    <td style={{ fontSize: 13 }}>{c.ward || "—"}</td>
                    <td style={{ fontSize: 13, color: c.severity_score >= 0.7 ? "#fca5a5" : c.severity_score >= 0.4 ? "#fcd34d" : "var(--text)" }}>{c.severity_score != null ? c.severity_score.toFixed(2) : "—"}</td>
                    <td style={{ fontSize: 13 }}>{c.priority ?? "—"}</td>
                    <td>
                      <div className="action-cell">
                        <select value={statusToSet[tid] || "in_progress"} onChange={e => setStatusToSet(m => ({ ...m, [tid]: e.target.value }))}>
                          {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s.replace(/_/g, " ")}</option>)}
                        </select>
                        <input value={deptToSet[tid] || ""} placeholder="Department (optional)" onChange={e => setDeptToSet(m => ({ ...m, [tid]: e.target.value }))} />
                        <input value={msgToSet[tid] || ""} placeholder="Note (optional)" onChange={e => setMsgToSet(m => ({ ...m, [tid]: e.target.value }))} />
                        <button className="btn btn-sm btn-primary" onClick={() => onUpdateStatus(tid)} id={`update-${tid}`}>Update Status</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {complaints.length === 0 && (
                <tr><td colSpan="7" style={{ color: "var(--muted)", padding: "24px", textAlign: "center" }}>No complaints found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
