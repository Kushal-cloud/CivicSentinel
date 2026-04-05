import React from "react";
import { MapContainer, TileLayer, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function HeatmapMap({ cells }) {
  const points = cells || [];
  const center = points[0]
    ? [points[0].lat_bin, points[0].lon_bin]
    : [20.5937, 78.9629]; // fallback: India center-ish

  return (
    <MapContainer center={center} zoom={12} style={{ height: 360, width: "100%" }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {points.map((c, idx) => (
        <CircleMarker
          key={idx}
          center={[c.lat_bin, c.lon_bin]}
          radius={Math.max(4, Math.min(40, c.count * 3))}
          pathOptions={{
            color: "#ff4d4d",
            fillColor: "#ff4d4d",
            fillOpacity: 0.35,
          }}
        />
      ))}
    </MapContainer>
  );
}

