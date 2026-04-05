import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { client } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";

const LANGUAGES = [
  { code: "en", label: "English" }, { code: "hi", label: "हिन्दी" },
  { code: "bn", label: "বাংলা" },  { code: "ta", label: "தமிழ்" },
  { code: "te", label: "తెలుగు" }, { code: "ml", label: "മലയാളം" },
  { code: "mr", label: "मराठी" },  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "gu", label: "ગુજરાતી" },{ code: "pa", label: "ਪੰਜਾਬੀ" },
  { code: "ur", label: "اردو" },
];

const TONES = [
  { value: "formal",    icon: "📃", label: "Formal",    desc: "Professional & polite" },
  { value: "urgent",    icon: "⚡", label: "Urgent",    desc: "Emphasize urgency" },
  { value: "escalated", icon: "🚨", label: "Escalated",  desc: "Demand executive action" },
];

export default function UploadPage() {
  const nav = useNavigate();
  const { user } = useAuth();
  const fileRef = useRef(null);

  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [manualWard, setManualWard] = useState("");
  const [manualLocality, setManualLocality] = useState("");
  const [description, setDescription] = useState("");
  const [language, setLanguage] = useState("en");
  const [tone, setTone] = useState("formal");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f && f.type.startsWith("image/")) handleFile(f);
  };

  const getGPS = () => {
    if (!navigator.geolocation) return;
    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const latVal = pos.coords.latitude.toFixed(6);
        const lonVal = pos.coords.longitude.toFixed(6);
        setLat(latVal);
        setLon(lonVal);
        try {
          const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latVal}&lon=${lonVal}&zoom=15&addressdetails=1`);
          if (res.ok) {
            const data = await res.json();
            const addr = data.address || {};
            const w = addr.city_district || addr.suburb || addr.neighbourhood || addr.borough || "";
            const l = addr.locality || addr.town || addr.village || addr.city || "";
            if (w) setManualWard(w);
            if (l) setManualLocality(l);
          }
        } catch (e) { console.log("Auto-detect location failed", e); }
        setGpsLoading(false);
      },
      () => setGpsLoading(false),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  const [wardLookupLoading, setWardLookupLoading] = useState(false);
  const [wardLookupMsg, setWardLookupMsg] = useState("");

  const lookupWardByLocality = async () => {
    if (!manualLocality.trim()) { setWardLookupMsg("Please enter a locality name first."); return; }
    setWardLookupLoading(true);
    setWardLookupMsg("");
    try {
      const query = encodeURIComponent(manualLocality.trim() + ", India");
      const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${query}&format=jsonv2&addressdetails=1&limit=1`);
      if (!res.ok) throw new Error("lookup failed");
      const results = await res.json();
      if (!results.length) { setWardLookupMsg("No results found for that locality."); return; }
      const addr = results[0].address || {};
      const ward = addr.city_district || addr.suburb || addr.neighbourhood || addr.borough || addr.county || "";
      const locality = addr.locality || addr.town || addr.village || addr.city || addr.state_district || "";
      const lat_ = results[0].lat;
      const lon_ = results[0].lon;
      if (ward) setManualWard(ward);
      if (locality) setManualLocality(locality);
      if (lat_) setLat(parseFloat(lat_).toFixed(6));
      if (lon_) setLon(parseFloat(lon_).toFixed(6));
      setWardLookupMsg(ward ? `✅ Ward identified: ${ward}` : "⚠️ Ward not found — filled what was available.");
    } catch (e) {
      setWardLookupMsg("Lookup failed. Check internet connection.");
    } finally {
      setWardLookupLoading(false);
    }
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    if (!file) { setErr("Please select an image."); return; }
    setBusy(true);
    try {
      const form = new FormData();
      form.append("image", file);
      if (lat) form.append("lat", String(lat));
      if (lon) form.append("lon", String(lon));
      if (manualWard) form.append("manual_ward", manualWard);
      if (manualLocality) form.append("manual_locality", manualLocality);
      if (description) form.append("citizen_description", description);
      form.append("language", language);
      form.append("tone", tone);
      const res = await client.post("/api/complaints/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
      nav(`/complaints/${res.data.tracking_id}`);
    } catch (ex) {
      setErr(ex?.response?.data?.detail || ex.message || "Upload failed. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container fade-up">
      <div className="page-header">
        <h2 className="page-title">Report a Civic Issue</h2>
        <div className="muted">Logged in as <strong style={{ color: "var(--text-secondary)" }}>{user?.email}</strong></div>
      </div>

      <form onSubmit={onSubmit} className="form">
        <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", gap: 20 }}>

          {/* Left column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Drop zone */}
            <div className="card">
              <div className="card-title" style={{ marginBottom: 14 }}>📸 Upload Image</div>

              {!preview ? (
                <div
                  id="dropzone"
                  className={`dropzone${dragOver ? " drag-over" : ""}`}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={onDrop}
                  onClick={() => fileRef.current?.click()}
                >
                  <div className="dropzone-icon">🖼️</div>
                  <div className="dropzone-text">Drop photo here or click to browse</div>
                  <div className="dropzone-hint">JPEG, PNG, WEBP · Max 8 MB</div>
                  <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }}
                    onChange={(e) => handleFile(e.target.files?.[0])} />
                </div>
              ) : (
                <div style={{ position: "relative" }}>
                  <img src={preview} alt="Preview" className="img-preview" />
                  <button type="button" onClick={() => { setFile(null); setPreview(null); }}
                    className="btn btn-sm" style={{ position: "absolute", top: 8, right: 8 }}>✕ Remove</button>
                </div>
              )}
            </div>

            {/* Location */}
            <div className="card">
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                <div className="card-title">📍 Location</div>
                <button type="button" className="btn btn-sm btn-primary" onClick={getGPS} disabled={gpsLoading} id="gps-btn">
                  {gpsLoading ? <><span className="spinner" style={{ width: 12, height: 12 }} /> Detecting…</> : "📡 Use GPS"}
                </button>
              </div>
              <div className="row2">
                <div>
                  <div className="muted small" style={{ marginBottom: 6 }}>Latitude</div>
                  <input value={lat} onChange={e => setLat(e.target.value)} placeholder="e.g. 28.6139" id="lat-input" />
                </div>
                <div>
                  <div className="muted small" style={{ marginBottom: 6 }}>Longitude</div>
                  <input value={lon} onChange={e => setLon(e.target.value)} placeholder="e.g. 77.2090" id="lon-input" />
                </div>
              </div>
              <div className="row2" style={{ marginTop: 12 }}>
                <div>
                  <div className="muted small" style={{ marginBottom: 6 }}>Locality Name</div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      value={manualLocality}
                      onChange={e => { setManualLocality(e.target.value); setWardLookupMsg(""); }}
                      placeholder="e.g. Connaught Place"
                      style={{ flex: 1 }}
                    />
                    <button type="button" className="btn btn-sm btn-primary" onClick={lookupWardByLocality} disabled={wardLookupLoading} title="Auto-identify ward from locality name">
                      {wardLookupLoading ? <span className="spinner" style={{ width: 11, height: 11 }} /> : "🔍 Find Ward"}
                    </button>
                  </div>
                  {wardLookupMsg && (
                    <div className="muted small" style={{ marginTop: 5, color: wardLookupMsg.startsWith("✅") ? "var(--success)" : "var(--warning)" }}>
                      {wardLookupMsg}
                    </div>
                  )}
                </div>
                <div>
                  <div className="muted small" style={{ marginBottom: 6 }}>Ward <span className="muted">(auto-filled or type)</span></div>
                  <input value={manualWard} onChange={e => setManualWard(e.target.value)} placeholder="Ward name" />
                </div>
              </div>
            </div>
          </div>

          {/* Right column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Description */}
            <div className="card">
              <div className="card-title" style={{ marginBottom: 14 }}>📝 Describe the Issue</div>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Describe what you see: when it started, safety concerns, nearby landmarks, how it affects people…"
                id="description-input"
              />
            </div>

            {/* Language */}
            <div className="card">
              <div className="card-title" style={{ marginBottom: 14 }}>🌐 Letter Language</div>
              <div className="lang-grid" id="lang-grid">
                {LANGUAGES.map(l => (
                  <button key={l.code} type="button"
                    className={`lang-pill${language === l.code ? " active" : ""}`}
                    onClick={() => setLanguage(l.code)} id={`lang-${l.code}`}>
                    {l.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tone */}
            <div className="card">
              <div className="card-title" style={{ marginBottom: 14 }}>🎭 Letter Tone</div>
              <div className="tone-cards">
                {TONES.map(t => (
                  <button key={t.value} type="button"
                    className={`tone-card${tone === t.value ? " active" : ""}`}
                    onClick={() => setTone(t.value)} id={`tone-${t.value}`}>
                    <div className="tone-card-icon">{t.icon}</div>
                    <div className="tone-card-label">{t.label}</div>
                    <div className="tone-card-desc">{t.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {err && <div className="error" style={{ marginTop: 16 }}>{err}</div>}

        <button className="primary" id="upload-submit-btn" disabled={!file || busy} style={{ marginTop: 20, maxWidth: 360 }}>
          {busy ? <><span className="spinner" /> Analysing image…</> : "🚀 Analyse & Generate Complaint"}
        </button>
      </form>
    </div>
  );
}
