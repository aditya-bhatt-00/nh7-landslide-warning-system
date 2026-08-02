"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import {
  CloudRain,
  AlertTriangle,
  ShieldAlert,
  PhoneCall,
  Bell,
  Mail,
  Phone,
  Radio,
  Globe,
} from "lucide-react";

// Dynamic import for Leaflet map to prevent SSR window errors
const MapComponent = dynamic(() => import("@/components/MapComponent"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[500px] bg-slate-900 animate-pulse rounded-lg flex items-center justify-center text-slate-400">
      Loading NH-7 GIS Map Engine...
    </div>
  ),
});

export default function Dashboard() {
  const [geoData, setGeoData] = useState<any>(null);
  const [weather, setWeather] = useState({ current_rain_mm_hr: 0, rain_24h_mm: 0 });
  const [counts, setCounts] = useState({ high: 0, moderate: 0, low: 0 });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [phone, setPhone] = useState("");
  const [language, setLanguage] = useState<"EN" | "HI">("EN");

  // Fetch telemetry and 500m GeoJSON route micro-segments from FastAPI backend
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/segments");
        if (res.ok) {
          const data = await res.json();
          setGeoData(data);

          // Direct telemetry parse from Open-Meteo payload
          if (data.telemetry) {
            setWeather({
              current_rain_mm_hr: data.telemetry.current_rain_mm_hr ?? 0,
              rain_24h_mm: data.telemetry.rain_24h_mm ?? 0,
            });
          }

          // Dynamic hazard counting across all 100 micro-segments
          let high = 0, mod = 0, low = 0;
          data.features?.forEach((f: any) => {
            const score = f.properties?.hazard_score || 0;
            if (score >= 0.7) high++;
            else if (score >= 0.4) mod++;
            else low++;
          });
          setCounts({ high, moderate: mod, low });
        }
      } catch (err) {
        console.error("Backend offline or connection issue:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // 30s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const handleSmsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    alert(`SMS alerts subscribed successfully for ${phone}!`);
    setIsModalOpen(false);
    setPhone("");
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      {/* HEADER */}
      <header className="bg-slate-900/90 border-b border-slate-800 px-6 py-3.5 flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              NH-7 Travel Safety & Landslide Alert System
            </h1>
            <p className="text-xs text-slate-400">
              Live corridor monitoring: Rudraprayag &rarr; Gauchar &rarr; Karnaprayag &rarr; Chamoli
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs rounded-lg shadow-md transition"
          >
            <Bell className="w-4 h-4" />
            {language === "EN" ? "Subscribe to SMS Alerts" : "SMS अलर्ट की सदस्यता लें"}
          </button>

          <button
            onClick={() => setLanguage(language === "EN" ? "HI" : "EN")}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 transition"
          >
            <Globe className="w-3.5 h-3.5" />
            {language === "EN" ? "हिंदी" : "English"}
          </button>
        </div>
      </header>

      {/* MAIN DASHBOARD CONTENT */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4">
        {/* LEFT SIDEBAR PANEL */}
        <aside className="lg:col-span-4 flex flex-col gap-4">
          {/* LIVE RAINFALL TELEMETRY */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-md">
            <div className="flex items-center gap-2 text-xs font-semibold text-sky-400 uppercase tracking-wider mb-3">
              <CloudRain className="w-4 h-4" />
              Live Rainfall Telemetry
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                <span className="text-[11px] text-slate-400 block mb-1">Current Rate</span>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-white">{weather.current_rain_mm_hr} mm/hr</span>
                  <span className="px-2 py-0.5 text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    Live
                  </span>
                </div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                <span className="text-[11px] text-slate-400 block mb-1">24-Hour Total</span>
                <span className="text-lg font-bold text-white">{weather.rain_24h_mm} mm</span>
              </div>
            </div>
          </div>

          {/* CORRIDOR THREAT BREAKDOWN */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-md">
            <div className="flex items-center gap-2 text-xs font-semibold text-amber-400 uppercase tracking-wider mb-3">
              <AlertTriangle className="w-4 h-4" />
              Corridor Threat Breakdown (500m Segments)
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-red-950/30 border border-red-800/50 rounded-lg p-2.5">
                <span className="text-xs font-medium text-red-400 block">High Risk</span>
                <span className="text-xl font-bold text-red-300">{counts.high}</span>
              </div>
              <div className="bg-amber-950/30 border border-amber-800/50 rounded-lg p-2.5">
                <span className="text-xs font-medium text-amber-400 block">Moderate</span>
                <span className="text-xl font-bold text-amber-300">{counts.moderate}</span>
              </div>
              <div className="bg-emerald-950/30 border border-emerald-800/50 rounded-lg p-2.5">
                <span className="text-xs font-medium text-emerald-400 block">Low Risk</span>
                <span className="text-xl font-bold text-emerald-300">{counts.low}</span>
              </div>
            </div>
          </div>

          {/* TRAVEL ADVISORY & SAFE SHELTERS */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-md">
            <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">
              <ShieldAlert className="w-4 h-4" />
              Travel Advisory & Safe Shelters
            </div>
            <p className="text-xs text-slate-300 mb-3">
              Night travel strictly restricted near active slides. Designated safe staging zones:
            </p>
            <ul className="space-y-2 text-xs">
              <li className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 flex items-center gap-2 text-slate-300">
                <Radio className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Gauchar Airstrip Compound</span>
              </li>
              <li className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800 flex items-center gap-2 text-slate-300">
                <Radio className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Karnaprayag Degree College Shelter</span>
              </li>
            </ul>
          </div>

          {/* EMERGENCY CONTACTS */}
          <div className="bg-red-950/20 border border-red-900/60 rounded-xl p-4 shadow-md">
            <div className="flex items-center gap-2 text-xs font-semibold text-red-400 uppercase tracking-wider mb-2">
              <PhoneCall className="w-4 h-4" />
              Emergency Contacts
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center bg-slate-950/80 p-2 rounded border border-red-900/40">
                <span className="text-slate-300">SDRF Hotline:</span>
                <span className="font-bold text-red-400">112 / 1070</span>
              </div>
              <div className="flex justify-between items-center bg-slate-950/80 p-2 rounded border border-red-900/40">
                <span className="text-slate-300">NDRF Control:</span>
                <span className="font-bold text-red-400">+91-9711077372</span>
              </div>
            </div>
          </div>

          {/* PROJECT DEVELOPER & FOOTER */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-md mt-auto">
            <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
              Project Developer & Contact
            </div>
            <p className="text-[11px] text-slate-400 mb-3">
              Geospatial AI early warning platform built for Uttarakhand highway disaster risk monitoring.
            </p>
            <div className="space-y-1.5 text-xs text-slate-300 mb-3">
              <div className="flex items-center gap-2">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                <span>aditya.bhatt.tech@gmail.com</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                <span>+91-8699037207</span>
              </div>
            </div>

            {/* Developer Social Links */}
            <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
              <a
                href="https://github.com/aditya-bhatt-00"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md transition border border-slate-700"
              >
                <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
                </svg>
                <span>GitHub</span>
              </a>

              <a
                href="https://linkedin.com/in/adityaaabhatt"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md transition border border-slate-700"
              >
                <svg className="w-3.5 h-3.5 fill-blue-400" viewBox="0 0 24 24">
                  <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
                </svg>
                <span>LinkedIn</span>
              </a>

              <a
                href="https://instagram.com/aditya_bhatt__"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md transition border border-slate-700"
              >
                <svg className="w-3.5 h-3.5 fill-pink-400" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
                <span>Instagram</span>
              </a>
            </div>
          </div>
        </aside>

        {/* RIGHT GIS MAP CONTAINER */}
        <main className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden min-h-[550px] shadow-lg">
          <MapComponent geoJsonData={geoData} />
        </main>
      </div>

      {/* SMS SUBSCRIPTION MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[2000] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-2">Subscribe to Live SMS Alerts</h3>
            <p className="text-xs text-slate-400 mb-4">
              Receive real-time automated SMS notifications whenever severe rainfall or landslide warnings are detected on NH-7.
            </p>
            <form onSubmit={handleSmsSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Mobile Number (with country code)
                </label>
                <input
                  type="text"
                  required
                  placeholder="+91 9876543210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg transition"
                >
                  Confirm Subscription
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}