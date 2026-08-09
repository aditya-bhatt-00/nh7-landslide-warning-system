# 🏔️ NH-7 Geospatial Landslide Early Warning System

A personal project that models a proactive, real-time approach to landslide risk monitoring on the NH-7 highway corridor in Uttarakhand. Built with FastAPI and Next.js, it divides the highway into 500m segments, scores each one using live weather telemetry, and pushes an automated Telegram alert when a segment crosses a hazard threshold.

This is an independent portfolio project, not an official system operated by or affiliated with SDRF/NDRF or any government body — public emergency numbers are surfaced on the dashboard purely as a convenience for users, not because those agencies use this tool.

🔗 [Live Dashboard](https://nh7-landslide-warning-system.vercel.app/)
🔗 [Backend API](https://nh7-landslide-warning-system.onrender.com/)

---

## 📖 The Idea & The Problem

The NH-7 (formerly NH-58) corridor between Rudraprayag and Chamoli is a critical lifeline for travelers, locals, pilgrims, and emergency logistics — and its mountainous terrain is highly exposed to intense monsoon rainfall and landslides.

Most disaster response in the region is reactive: action follows a blockage, not the conditions that cause one. This project explores what a proactive, low-cost early-warning layer could look like — using live weather data and simple geospatial segmentation to flag risk *before* it becomes a blockage, rather than claiming to replace the systems and personnel who actually manage highway safety in the region.

---

## ⚙️ How It Works (System Architecture)

1. **Precision Micro-segmentation** — The highway route is digitally mapped and divided into ~69 discrete 500m segments from Rudraprayag to Chamoli using coordinate interpolation.
2. **Server-Side Telemetry Caching** — A background `asyncio` task refreshes live rainfall data from Open-Meteo every 5 minutes and stores it in a shared in-memory cache. Every API request reads from this cache instead of making a live call per request — this avoids rate-limiting under load and keeps response times fast.
3. **Dynamic Hazard Scoring** — Each segment gets a hazard score combining a fixed geographic baseline with the current rainfall multiplier (live rate + rolling 24h accumulation).
4. **Automated Dispatch** — When a segment crosses the high-risk threshold, an integrated Telegram Bot pushes a formatted alert with the affected chainage.
5. **GIS Visualization** — The dashboard renders live hazard states on an interactive Leaflet map, alongside designated safe staging zones (e.g. Gauchar Airstrip Compound, Karnaprayag Degree College Shelter).

---

## ✨ Key Features

- **Live Telemetry & Risk Matrix** — Real-time rainfall monitoring (current rate + 24h total) feeding into per-segment hazard scores, with a `telemetry.status` field (`ok` / `stale` / `error`) so the UI never silently displays failed-fetch data as if it were live.
- **Interactive Leaflet GIS Map** — Color-coded segment rendering (Red = High, Orange = Moderate, Green = Low).
- **Automated Telegram Dispatch** — Threshold-triggered alerts with corridor chainage and staging-zone info.
- **Bilingual UI** — English / Hindi toggle for key dashboard info.
- **Simulation Mode** — `?simulate_rain=true` demonstrates high-threat UI states without waiting for real severe weather.

---

## 🛠️ Tech Stack

**Frontend** (Vercel)
- Next.js (React)
- React-Leaflet
- Tailwind CSS
- Lucide-react

**Backend** (Render)
- FastAPI (Python)
- `asyncio` background task for scheduled telemetry refresh (replaces per-request live fetches)
- Python `math` module for coordinate interpolation / segment generation

---

## 🗄️ Data Sources & Integrations

- **Weather Telemetry:** [Open-Meteo API](https://open-meteo.com/en/docs) — free, no-key precipitation data
- **Alerting:** [Telegram Bot API](https://core.telegram.org/bots/api)
- **Mapping:** [OpenStreetMap](https://www.openstreetmap.org/) via Leaflet tile layers

---

## 🧩 Engineering Notes

A real bug worth documenting: the production deployment on Render was silently returning `0 mm/hr` and `0 mm` for rainfall on every request, even though local development showed real data. Root cause — every client's 30-second dashboard poll was triggering a fresh live call to Open-Meteo directly inside the request handler, and any failure in that call (timeout, rate limit, transient error) silently defaulted rainfall to `0.0` with no visibility into why. Fixed by moving the fetch to a single scheduled background task with retries and a `status` field surfaced in the API response, so the frontend now distinguishes real live data from a stale/failed fetch instead of quietly showing zero as if it were current.

---

## 🚀 Getting Started (Local Setup)

```bash
git clone https://github.com/aditya-bhatt-00/nh7-landslide-warning-system.git
cd nh7-landslide-warning-system
```

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` in the frontend's environment to point at your backend (defaults to `http://127.0.0.1:8000` locally).

---

## ⚠️ Disclaimer

This is a portfolio/demonstration project and is not a substitute for official disaster-management infrastructure, real-time government advisories, or professional emergency response. Do not rely on it for actual travel safety decisions.
