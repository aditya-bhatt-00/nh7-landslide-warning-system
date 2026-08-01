# 🏔️ LandslideGuard NH-58: Dynamic Spatial Early Warning System

An end-to-end Geospatial AI and real-time decision support system designed to predict and monitor landslide hazards along a critical 50km stretch of National Highway 58 (Rudraprayag to Chamoli, Uttarakhand, India).

![License](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)

---

## 🎯 Goal & Problem Statement

National Highway 58 (NH-58) is a lifeline corridor in the Garhwal Himalayas of Uttarakhand, connecting key pilgrimage destinations (Kedarnath, Badrinath, Hemkund Sahib) and strategic border regions. However, intense monsoon precipitation, unstable steep slopes, and active undercut erosion regularly trigger destructive slope failures, isolating towns and stranding commuters.

**LandslideGuard NH-58** addresses this challenge by combining static geomorphic slope parameters with live precipitation telemetry to produce a **Dynamic Landslide Risk Index (DLRI)**. The goal is to provide local citizens, drivers, and disaster response teams with actionable, clear, and real-time highway risk advisories.

---

## 📊 Dataset & Spatial Features

This project integrates multi-source geospatial data covering the Rudraprayag–Chamoli corridor:

| Dataset / Source | Type | Description | Usage in Pipeline |
| :--- | :--- | :--- | :--- |
| **USGS / ISRO Bhuvan DEM** | Raster (30m DEM) | Digital Elevation Model of the Alaknanda River Basin | Elevation, slope angle extraction, and aspect derivation |
| **OpenStreetMap (OSM)** | Vector (LineString) | NH-58 Highway Geometry & Hydrographic network | Segmented into 500m micro-corridor evaluation vectors |
| **GSI Landslide Inventory** | Vector (Point/Polygon) | Historical landslide failure sites in Uttarakhand | Spatial proximity calculations (`dist_to_landslide_m`) |
| **Open-Meteo API** | REST / JSON | Live precipitation and 24h forecast telemetry | Real-time dynamic risk calculation |

---

## ⚙️ Methodology & Architecture

### 1. Spatial Preprocessing & Feature Engineering
- **Corridor Vectorization**: Segmented the 50km highway vector into 131 uniform 500m evaluation units.
- **Topographic Risk Scoring**: Extracted slope gradients (`mean_slope_deg`, `max_slope_deg`), elevation metrics, distance to rivers (`dist_to_river_m`), and distance to historic slope failures (`dist_to_landslide_m`).

### 2. Machine Learning Engine
- **Model**: Trained an **XGBoost Classifier** to determine baseline terrain vulnerability.
- **Explainability**: Integrated **SHAP (SHapley Additive exPlanations)** to interpret key drivers of slope instability.
- **Performance**: Achieved an **ROC-AUC score of 1.00** and **96% Test Accuracy** on the baseline corridor dataset.

### 3. Dynamic Landslide Risk Index (DLRI)
Static topography is combined with live precipitation data using the following composite formula:

$$\text{DLRI} = (\text{Static Topographic Hazard Probability} \times 0.6) + (\text{Rainfall Factor} \times 0.4)$$

Where the **Rainfall Factor** is calculated dynamically from live 24-hour accumulated rainfall ($\text{Rainfall Factor} = \min(\text{Rain}_{24h} / 50.0, 1.0)$).

---

## 💻 Tech Stack

- **Data Science & GIS**: Python, GeoPandas, Shapely, Rasterio, XGBoost, Scikit-Learn, SHAP
- **Backend API**: FastAPI, Uvicorn, Requests, Pydantic
- **Frontend Dashboard**: Next.js (React), TailwindCSS, Leaflet.js, Lucide Icons

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Clone & Set Up Backend

```bash
git clone [https://github.com/your-username/landslide-guard-nh58.git](https://github.com/your-username/landslide-guard-nh58.git)
cd landslide-guard-nh58

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch FastAPI backend
uvicorn app:app --reload