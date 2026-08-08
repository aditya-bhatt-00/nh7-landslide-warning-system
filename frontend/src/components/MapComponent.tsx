"use client";

import { useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet's default marker icon paths in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface MapProps {
  geoJsonData: any;
}

export default function MapComponent({ geoJsonData }: MapProps) {
  // Style each line segment based on hazard_score from backend
  const styleSegment = (feature: any) => {
    const score = feature.properties?.hazard_score || 0;
    let color = "#10B981"; // Low Risk (Green)

    if (score >= 0.7) {
      color = "#EF4444"; // High Risk (Red)
    } else if (score >= 0.4) {
      color = "#F59E0B"; // Moderate Risk (Orange/Amber)
    }

    return {
      color: color,
      weight: 6,
      opacity: 0.95,
      lineCap: "round" as const,
      lineJoin: "round" as const,
    };
  };

  const onEachFeature = (feature: any, layer: L.Layer) => {
    if (feature.properties) {
      const { segment_id, hazard_score, weather_summary } = feature.properties;
      const popupContent = `
        <div style="font-family: sans-serif; padding: 4px;">
          <h4 style="margin: 0 0 6px 0; font-size: 14px; font-weight: bold;">
            Segment: ${segment_id || "NH-58 Route"}
          </h4>
          <p style="margin: 2px 0; font-size: 12px;">
            <strong>Hazard Risk:</strong> ${(hazard_score * 100).toFixed(0)}%
          </p>
          <p style="margin: 2px 0; font-size: 12px;">
            <strong>Telemetry:</strong> ${weather_summary || "Live Open-Meteo Feed"}
          </p>
        </div>
      `;
      layer.bindPopup(popupContent);
    }
  };

  return (
    <div className="relative w-full h-full min-h-[500px]">
      <MapContainer
        center={[30.3165, 78.9629]}
        zoom={10}
        scrollWheelZoom={true}
        className="w-full h-full rounded-lg z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {geoJsonData && geoJsonData.type === "FeatureCollection" && geoJsonData.features && (
  <GeoJSON
    key={JSON.stringify(geoJsonData)}
    data={geoJsonData}
    style={styleSegment}
  />
)}
      </MapContainer>

      {/* Floating Map Legend Overlay */}
      <div className="absolute bottom-6 right-6 z-[1000] bg-slate-900/90 backdrop-blur-md p-3.5 rounded-lg border border-slate-700 shadow-2xl text-xs text-slate-200 pointer-events-auto">
        <p className="font-semibold mb-2 text-slate-400 uppercase tracking-wider text-[11px]">
          Highway Risk Legend
        </p>
        <div className="space-y-2">
          <div className="flex items-center gap-2.5">
            <span className="w-4 h-1.5 bg-red-500 rounded-full shadow-sm"></span>
            <span className="font-medium text-slate-200">High Risk (&gt; 70%)</span>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="w-4 h-1.5 bg-amber-500 rounded-full shadow-sm"></span>
            <span className="font-medium text-slate-200">Moderate Risk (40% - 70%)</span>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="w-4 h-1.5 bg-emerald-500 rounded-full shadow-sm"></span>
            <span className="font-medium text-slate-200">Low Risk (&lt; 40%)</span>
          </div>
        </div>
      </div>
    </div>
  );
}