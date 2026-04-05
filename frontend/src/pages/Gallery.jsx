import React, { useEffect, useState } from "react";
import { client } from "../api/client.js";

export default function Gallery() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await client.get("/api/complaints/public/gallery");
        setComplaints(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div className="container" style={{ padding: "40px" }}><div className="spinner" /> Loading gallery...</div>;

  return (
    <div className="container fade-up">
      <div className="page-header" style={{ marginBottom: 30 }}>
        <h2 className="page-title">✨ Success Gallery</h2>
        <div className="muted">See how civic issues are being resolved across the community.</div>
      </div>

      {complaints.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "60px 20px" }}>
            <div style={{ fontSize: 40, marginBottom: 10 }}>🏗️</div>
            <h4>No resolved issues yet!</h4>
            <div className="muted">Check back later when issues start getting fixed.</div>
        </div>
      ) : (
        <div className="gallery-grid">
          {complaints.map(c => (
            <div key={c.tracking_id} className="card gallery-card">
              <div className="gallery-images">
                 <div className="before-img-container">
                    <span className="img-label">Before</span>
                    <img src={`/api/uploads/${c.image_path}`} alt="Before" className="gallery-img" onError={(e)=>{e.target.src="https://via.placeholder.com/300?text=Image+Missing"}}/>
                 </div>
                 <div className="after-img-container">
                    <span className="img-label bg-success">After</span>
                    {c.resolved_image_path ? 
                        <img src={`/api/uploads/${c.resolved_image_path}`} alt="After" className="gallery-img" onError={(e)=>{e.target.src="https://via.placeholder.com/300?text=Image+Missing"}}/>
                        : <div className="gallery-placeholder">Resolved by Authority</div>
                    }
                 </div>
              </div>
              <div className="gallery-info">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <strong>{c.issue_category?.replace("_", " ").toUpperCase() || "ISSUE"}</strong>
                      <span className="badge badge-success">Fixed</span>
                  </div>
                  <div className="muted small" style={{ marginTop: 6}}>📍 {c.locality || "Unknown"}, {c.ward || ""}</div>
                  <div className="muted small" style={{ marginTop: 6}}>👍 {c.upvotes || 0} Upvotes</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
