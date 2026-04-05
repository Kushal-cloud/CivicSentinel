import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { client } from "../api/client.js";
import StatusTimeline from "../components/StatusTimeline.jsx";
import { useAuth } from "../auth/AuthContext.jsx";
import jsPDF from "jspdf";

const LANGUAGES = [
  { code: "en", label: "English" }, { code: "hi", label: "हिन्दी" },
  { code: "bn", label: "বাংলা" },  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" }, { code: "ml", label: "മലയാളം" },
  { code: "mr", label: "मराठी" },  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "gu", label: "ગુજરાતી" },{ code: "pa", label: "ਪੰਜਾਬੀ" },
  { code: "ur", label: "اردو" },
];

const TONES = [
  { value: "formal", label: "📃 Formal" },
  { value: "urgent", label: "⚡ Urgent" },
  { value: "escalated", label: "🚨 Escalated" },
];

function statusBadgeClass(status) {
  const map = {
    received: "badge status-received",
    review_pending: "badge status-review_pending",
    ready_for_submission: "badge status-ready_for_submission",
    submitted: "badge status-submitted",
    in_progress: "badge status-in_progress",
    resolved: "badge status-resolved",
    escalated: "badge status-escalated",
    rejected: "badge status-rejected",
    flagged: "badge status-flagged",
  };
  return map[status] || "badge badge-muted";
}

function statusLabel(status) {
  return (status || "").replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

export default function ComplaintPage() {
  const { trackingId } = useParams();
  const { role } = useAuth();

  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [complaint, setComplaint] = useState(null);
  const [events, setEvents] = useState([]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [language, setLanguage] = useState("en");
  const [tone, setTone] = useState("formal");
  const [copied, setCopied] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);

  const canEdit = useMemo(() => {
    if (!complaint) return false;
    return ["review_pending", "received", "flagged"].includes(complaint.status);
  }, [complaint]);

  const refresh = useCallback(async () => {
    setErr("");
    setLoading(true);
    try {
      const [res, ev] = await Promise.all([
        client.get(`/api/complaints/${trackingId}`),
        client.get(`/api/complaints/citizen/${trackingId}/events`),
      ]);
      setComplaint(res.data);
      setSubject(res.data.letter_draft_subject || "");
      setBody(res.data.letter_draft_body || "");
      setLanguage(res.data.language || "en");
      setTone(res.data.tone || "formal");
      setEvents(ev.data || []);
    } catch (ex) {
      setErr(ex?.response?.data?.detail || ex.message || "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [trackingId]);

  useEffect(() => { refresh(); }, [refresh]);

  const approve = async () => {
    setErr(""); setActionBusy(true);
    try {
      await client.put(`/api/complaints/${trackingId}/review`, { approve: true, letter_draft_subject: subject, letter_draft_body: body, language, tone });
      await refresh();
    } catch (ex) { setErr(ex?.response?.data?.detail || ex.message || "Approve failed"); }
    finally { setActionBusy(false); }
  };

  const regenerate = async () => {
    setErr(""); setActionBusy(true);
    try {
      await client.post(`/api/complaints/${trackingId}/regenerate`, { language, tone });
      await refresh();
    } catch (ex) { setErr(ex?.response?.data?.detail || ex.message || "Regenerate failed"); }
    finally { setActionBusy(false); }
  };

  const submit = async () => {
    setErr(""); setActionBusy(true);
    try {
      await client.post(`/api/complaints/${trackingId}/submit`);
      await refresh();
    } catch (ex) { setErr(ex?.response?.data?.detail || ex.message || "Submit failed"); }
    finally { setActionBusy(false); }
  };

  const upvote = async () => {
    setActionBusy(true);
    try {
      await client.post(`/api/complaints/${trackingId}/upvote`);
      await refresh();
    } catch (e) { setErr("Upvote failed: " + e.message); }
    finally { setActionBusy(false); }
  };

  const sendFollowUp = async () => {
    setActionBusy(true);
    try {
      await client.post(`/api/complaints/${trackingId}/follow-up`);
      await refresh();
    } catch (e) { setErr("Follow up failed: " + e.message); }
    finally { setActionBusy(false); }
  };

  const generatePDF = async () => {
    setActionBusy(true);
    try {
      const doc = new jsPDF({ unit: "mm", format: "a4" });
      const pageW = doc.internal.pageSize.getWidth();
      const margin = 20;
      const usableW = pageW - margin * 2;

      doc.setFillColor(124, 58, 237);
      doc.rect(0, 0, pageW, 22, "F");
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(13);
      doc.setFont("helvetica", "bold");
      doc.text("CivicSentinel — Verified Complaint Evidence", margin, 14);
      doc.setTextColor(30, 30, 30);
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      let y = 32;

      const fieldRow = (label, val) => {
        doc.setFont("helvetica", "bold");
        doc.text(label + ":", margin, y);
        doc.setFont("helvetica", "normal");
        const lines = doc.splitTextToSize(String(val || "—"), usableW - 50);
        doc.text(lines, margin + 47, y);
        y += lines.length * 6 + 1;
      };
      fieldRow("Tracking ID", trackingId);
      fieldRow("Generated At", new Date().toLocaleString());
      fieldRow("Reporter", complaint.reporter_name || "Unknown");
      fieldRow("Location", [complaint.locality, complaint.ward, complaint.jurisdiction].filter(Boolean).join(", ") || "Unknown");
      fieldRow("Issue Category", (complaint.issue_category || "").replace(/_/g, " ").toUpperCase());
      fieldRow("Severity Score", complaint.severity_score != null ? complaint.severity_score.toFixed(2) : "N/A");
      fieldRow("Status", (complaint.status || "").replace(/_/g, " ").toUpperCase());

      y += 5;
      doc.setDrawColor(180, 180, 200);
      doc.line(margin, y, pageW - margin, y);
      y += 8;

      if (complaint.image_path) {
        const imgPath = (complaint.image_path || "").split("/").pop();
        const imgUrl = `/api/uploads/${imgPath}`;
        const imgResult = await new Promise((resolve) => {
          const i = new Image();
          i.crossOrigin = "anonymous";
          i.onload = () => resolve(i);
          i.onerror = () => resolve(null);
          setTimeout(() => resolve(null), 6000);
          i.src = imgUrl;
        });
        if (imgResult) {
          const ratio = imgResult.height / imgResult.width;
          const imgW = Math.min(80, usableW * 0.5);
          const imgH = imgW * ratio;
          doc.setFont("helvetica", "bold");
          doc.text("Evidence Photo:", margin, y);
          y += 5;
          doc.addImage(imgResult, "JPEG", margin, y, imgW, imgH);
          y += imgH + 10;
        } else {
          doc.setFontSize(9);
          doc.setTextColor(150, 150, 150);
          doc.text("[Evidence photo could not be embedded]", margin, y);
          doc.setTextColor(30, 30, 30);
          doc.setFontSize(10);
          y += 8;
        }
      }

      doc.addPage();
      doc.setFillColor(124, 58, 237);
      doc.rect(0, 0, pageW, 22, "F");
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(13);
      doc.setFont("helvetica", "bold");
      doc.text("AI-Processed Complaint Letter", margin, 14);
      doc.setTextColor(30, 30, 30);
      doc.setFontSize(10);
      y = 32;

      if (subject) {
        doc.setFont("helvetica", "bold");
        const subjectLines = doc.splitTextToSize(subject, usableW);
        doc.text(subjectLines, margin, y);
        y += subjectLines.length * 6 + 4;
        doc.setDrawColor(180, 180, 200);
        doc.line(margin, y, pageW - margin, y);
        y += 6;
      }
      if (body) {
        doc.setFont("helvetica", "normal");
        const bodyLines = doc.splitTextToSize(body, usableW);
        const lineH = 5.5;
        const pageH = doc.internal.pageSize.getHeight();
        for (const line of bodyLines) {
          if (y + lineH > pageH - margin) { doc.addPage(); y = margin; }
          doc.text(line, margin, y);
          y += lineH;
        }
      }

      doc.save(`${trackingId}_evidence.pdf`);
    } catch (e) {
      console.error("PDF error:", e);
      setErr("PDF generation failed: " + e.message);
    } finally {
      setActionBusy(false);
    }
  };
  const copyLetter = () => {
    navigator.clipboard.writeText(`${subject}\n\n${body}`).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  if (loading) return (
    <div className="container loading-screen">
      <div className="loading-spinner" />
      <div className="muted">Loading complaint…</div>
    </div>
  );

  if (!complaint) return <div className="container"><div className="error">Complaint not found.</div></div>;

  const sev = complaint.severity_score;
  const sevColor = sev >= 0.7 ? "#fca5a5" : sev >= 0.4 ? "#fcd34d" : "#6ee7b7";

  return (
    <div className="container fade-up">
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24, gap: 16, flexWrap: "wrap" }}>
        <div>
          <div className="muted small" style={{ marginBottom: 6 }}>Complaint Report</div>
          <h2 className="page-title" style={{ fontSize: 20, display: "flex", alignItems: "center", gap: 12 }}>
            <span className="mono" style={{ color: "var(--primary-light)" }}>{trackingId}</span>
            <span className={statusBadgeClass(complaint.status)}>{statusLabel(complaint.status)}</span>
            {complaint.fraud_flag && <span className="badge badge-danger">⚠️ Flagged</span>}
          </h2>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
            <button className="btn btn-primary btn-sm" onClick={upvote}>👍 Upvote ({complaint.upvotes || 0})</button>
            <button className="btn btn-primary btn-sm" onClick={generatePDF}>📄 Export Evidence PDF</button>
            {role === "admin" && (
              <a href="/admin" className="btn btn-sm btn-primary">← Admin Dashboard</a>
            )}
        </div>
      </div>

      {err && <div className="error">{err}</div>}

      <div className="complaint-layout">
        {/* Sidebar */}
        <div className="complaint-sidebar">
          {/* AI Detection */}
          <div className="card">
            <div className="card-title" style={{ marginBottom: 16 }}>🤖 AI Detection</div>
            <div className="kv">
              <div className="kv-row">
                <span className="kv-key">Category</span>
                <span className="kv-val">{(complaint.issue_category || "unknown").replace(/_/g, " ")}</span>
              </div>
              <div className="kv-row">
                <span className="kv-key">Department</span>
                <span className="kv-val" style={{ fontSize: 12 }}>{complaint.department_name || "—"}</span>
              </div>
              <div className="kv-row">
                <span className="kv-key">Severity</span>
                <span className="kv-val" style={{ color: sevColor }}>{sev != null ? sev.toFixed(2) : "—"}</span>
              </div>
              <div className="kv-row">
                <span className="kv-key">Priority</span>
                <span className="kv-val">{complaint.priority ?? "—"}</span>
              </div>
              <div className="kv-row">
                <span className="kv-key">Location</span>
                <span className="kv-val" style={{ fontSize: 12 }}>{[complaint.ward, complaint.locality].filter(Boolean).join(" / ") || "—"}</span>
              </div>
              <div className="kv-row">
                <span className="kv-key">Jurisdiction</span>
                <span className="kv-val" style={{ fontSize: 12 }}>{complaint.jurisdiction || "—"}</span>
              </div>
              <div className="kv-row">
                <span className="kv-key">Duplicate</span>
                <span className="kv-val">{complaint.duplicate_of_tracking_id || "None"}</span>
              </div>
            </div>

            {complaint.detected_issues?.detections?.length > 0 && (
              <>
                <div className="divider" />
                <div className="muted small" style={{ marginBottom: 8 }}>Detected issues</div>
                <div className="chips">
                  {complaint.detected_issues.detections.map((d, i) => (
                    <div key={i} className="chip">{d.class_name} ({Math.round((d.confidence || 0) * 100)}%)</div>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Timeline */}
          <div className="card">
            <div className="card-title" style={{ marginBottom: 16 }}>📋 Status Timeline</div>
            <StatusTimeline events={events} />
          </div>
        </div>

        {/* Main Editor */}
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18, flexWrap: "wrap", gap: 10 }}>
            <div className="card-title">✍️ Complaint Letter</div>
            <button type="button" className="btn btn-sm" onClick={copyLetter} id="copy-btn">
              {copied ? "✅ Copied!" : "📋 Copy Letter"}
            </button>
          </div>

          {/* Language + Tone */}
          <div style={{ marginBottom: 16 }}>
            <div className="muted small" style={{ marginBottom: 8 }}>Language</div>
            <div className="lang-grid" id="complaint-lang-grid">
              {LANGUAGES.map(l => (
                <button key={l.code} type="button"
                  className={`lang-pill${language === l.code ? " active" : ""}`}
                  onClick={() => setLanguage(l.code)}
                  disabled={!canEdit}
                  id={`complaint-lang-${l.code}`}>
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div className="muted small" style={{ marginBottom: 8 }}>Tone</div>
            <div style={{ display: "flex", gap: 8 }}>
              {TONES.map(t => (
                <button key={t.value} type="button"
                  className={`lang-pill${tone === t.value ? " active" : ""}`}
                  onClick={() => setTone(t.value)}
                  disabled={!canEdit}
                  id={`complaint-tone-${t.value}`}>
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Subject */}
          <div style={{ marginBottom: 12 }}>
            <div className="muted small" style={{ marginBottom: 6 }}>Subject</div>
            <input
              value={subject}
              onChange={e => setSubject(e.target.value)}
              disabled={!canEdit}
              id="letter-subject"
              style={{ width: "100%", background: "var(--input-bg)", border: "1px solid var(--border)", color: "var(--text)", padding: "10px 14px", borderRadius: 8, outline: "none", fontFamily: "Inter, sans-serif", fontSize: 14 }}
            />
          </div>

          {/* Body */}
          <div>
            <div className="muted small" style={{ marginBottom: 6 }}>Letter Body</div>
            <textarea
              value={body}
              onChange={e => setBody(e.target.value)}
              disabled={!canEdit}
              rows={16}
              id="letter-body"
              className="letter-editor"
            />
          </div>

          {complaint.fraud_flag && (
            <div className="notice" style={{ marginTop: 14 }}>
              ⚠️ This report was flagged for potential spam/fraud. Submission is blocked pending admin review.
            </div>
          )}

          {/* Actions */}
          <div style={{ display: "flex", gap: 10, marginTop: 18, flexWrap: "wrap" }}>
            <button className="btn btn-success" onClick={approve} disabled={!canEdit || actionBusy} id="approve-btn">
              {actionBusy ? <span className="spinner" style={{ width: 13, height: 13 }} /> : "✅"} Approve
            </button>
            <button className="btn btn-primary" onClick={regenerate} disabled={!canEdit || actionBusy} id="regenerate-btn">
              🔄 Regenerate
            </button>
            <button className="btn btn-danger" onClick={submit}
              disabled={complaint.status !== "ready_for_submission" || actionBusy} id="submit-btn">
              📨 Submit to Authority
            </button>
            {complaint.status !== "resolved" && (
                <button className="btn btn-warning" onClick={sendFollowUp} disabled={actionBusy}>
                   🚨 Send Follow-up ({complaint.follow_up_count || 0})
                </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
