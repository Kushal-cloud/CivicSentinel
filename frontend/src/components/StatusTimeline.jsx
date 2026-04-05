import React from "react";

const EVENT_META = {
  uploaded:          { dot: "timeline-dot-violet", icon: "📎", label: "Uploaded" },
  ai_processed:      { dot: "timeline-dot-success", icon: "🤖", label: "AI Processed" },
  review_approved:   { dot: "timeline-dot-success", icon: "✅", label: "Approved" },
  review_pending:    { dot: "timeline-dot-warning", icon: "✏️", label: "Updated" },
  letter_regenerated:{ dot: "timeline-dot-violet",  icon: "🔄", label: "Regenerated" },
  submitted:         { dot: "timeline-dot-success", icon: "📨", label: "Submitted" },
  status_updated:    { dot: "timeline-dot-warning", icon: "🔔", label: "Status Updated" },
  escalated:         { dot: "timeline-dot-danger",  icon: "🚨", label: "Escalated" },
};

export default function StatusTimeline({ events }) {
  if (!events || events.length === 0)
    return <div className="muted" style={{ padding: "12px 0" }}>No events yet.</div>;

  const sorted = [...events].sort((a, b) =>
    (a.created_at || "").localeCompare(b.created_at || "")
  );

  return (
    <div className="timeline fade-up">
      {sorted.map((e) => {
        const meta = EVENT_META[e.event_type] || { dot: "timeline-dot-muted", icon: "•", label: e.event_type };
        return (
          <div key={e.id} className="timeline-item">
            <div className={`timeline-dot ${meta.dot}`} />
            <div className="timeline-time">
              {e.created_at ? new Date(e.created_at).toLocaleString() : ""}
            </div>
            <div className="timeline-event">
              <span>{meta.icon}</span>
              <span className="badge badge-muted" style={{ fontSize: 11 }}>{meta.label}</span>
            </div>
            {e.message && <div className="timeline-msg">{e.message}</div>}
          </div>
        );
      })}
    </div>
  );
}
