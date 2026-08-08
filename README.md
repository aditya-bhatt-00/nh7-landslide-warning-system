# 🏔️ NH-7 Geospatial Landslide Early Warning System

![Live Status](https://img.shields.io/badge/Status-Live-success)
![Frontend](https://img.shields.io/badge/Frontend-Next.js-black)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)
![Deployment](https://img.shields.io/badge/Deployed_on-Vercel_%7C_Render-blue)

The **NH-7 Landslide Early Warning System** protects Uttarakhand commuters using real-time GIS monitoring. Built with **FastAPI** and **Next.js**, it divides the highway into 500m segments to analyze live weather telemetry. When hazard thresholds are breached, an integrated automated Telegram bot dispatches instant safety alerts to prevent disasters and save lives.

🔗 **[Live Dashboard / Website](https://nh7-landslide-warning-system.vercel.app)**  
🔗 **[Backend API Endpoint](https://nh7-landslide-warning-system.onrender.com)**  

---

## 📖 The Idea & The Problem

The NH-7 (formerly NH-58) corridor stretching from **Rudraprayag to Chamoli** in Uttarakhand is a critical lifeline for travelers, locals, pilgrims, and emergency logistics. However, this mountainous terrain is highly susceptible to extreme weather, intense rainfall, flash floods, and catastrophic landslides. 

Historically, disaster management in this region has been **reactive**—acting only after a landslide blocks the road or damages property.

> **The Goal:** Shift from disaster response to **proactive disaster prevention**. By leveraging geospatial mapping and continuous environmental telemetry, this system detects unsafe conditions before they result in blockages or loss of life, providing local authorities (**SDRF/NDRF**) and commuters with actionable early warnings.

---

## ⚙️ How It Works (System Architecture)

This project is decoupled into a high-performance background monitoring backend and an interactive frontend dashboard.

1. **Precision Micro-segmentation:** The highway route is digitally mapped and divided into discrete **500-meter micro-segments** from Rudraprayag to Chamoli.
2. **Continuous Telemetry:** A persistent `asyncio` background task on the server fetches live environmental and rainfall data every 5 minutes, 24/7.
3. **Dynamic Hazard Scoring:** Each 500m segment is assigned a real-time risk score (**Low**, **Moderate**, **High**) based on localized rainfall intensity (mm/hr) and 24-hour accumulation.
4. **Instant Automated Alerts:** If a segment's hazard score breaches critical safety thresholds, the system's integrated **Telegram Bot** instantly pushes an emergency dispatch alert to subscribers.
5. **GIS Visualization:** The web dashboard plots live hazard states over an interactive geographic map, pinpointing current threat zones alongside designated **Safe Staging Zones** (e.g., *Gauchar Airstrip Compound* & *Karnaprayag Degree College Shelter*).

---

## ✨ Key Features

* **Live Telemetry & Risk Matrix:** Real-time rainfall monitoring (Current Rate & 24h Total) integrated into dynamic segment hazard scores.
* **Interactive Leaflet GIS Map:** Color-coded highway segment rendering (**Red** = High Risk, **Orange** = Moderate Risk, **Green** = Low Risk).
* **Direct Emergency Dispatch:** Instant notification routing via Telegram Bot API with SDRF/NDRF helpline details.
* **Bilingual Support & UI Controls:** Instant English / Hindi language toggle and quick SMS/Telegram subscription modal.

---

## 🛠️ Tech Stack

### Frontend (Deployed on Vercel)
* **Framework:** Next.js (React Framework)
* **Map Engine:** Leaflet / React-Leaflet
* **Styling:** Tailwind CSS
* **Icons:** Lucide-React

### Backend (Deployed on Render)
* **Framework:** FastAPI (Python)
* **Async Processing:** `asyncio` for persistent background tasks independent of web traffic
* **Geospatial Processing:** Python `math` module for coordinate interpolation and 500m segment generation

---

## 🗄️ Data Sources & Integrations

* **Weather & Environmental Telemetry:** [Open-Meteo API](https://open-meteo.com/en/docs) (Live localized precipitation & hourly forecast data)
* **Alerting Infrastructure:** [Telegram Bot API](https://core.telegram.org/bots/api) (Instant, lightweight message dispatch)
* **Mapping/GIS:** [OpenStreetMap](https://www.openstreetmap.org/) via Leaflet tile layers

---

## 🚀 Getting Started (Local Setup)

Follow these steps to run the complete system locally on your machine:

### 1. Clone the Repository
```bash
git clone [https://github.com/aditya-bhatt-00/nh7-landslide-warning-system.git](https://github.com/aditya-bhatt-00/nh7-landslide-warning-system.git)
cd nh7-landslide-warning-system