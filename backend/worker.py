import asyncio
import requests
import math
import time
import os

# ==========================================
# TELEGRAM CONFIGURATION
# ==========================================
# We use os.getenv so we don't hardcode sensitive keys in GitHub
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") 
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_alert(message_body):
    """Sends a push notification to Telegram using Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials not found in environment variables.")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message_body,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            print("Telegram Alert sent successfully!")
        else:
            print(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"Telegram Request Error: {e}")

# Geographic coordinate path for NH-7
NH7_ANCHOR_WAYPOINTS = [
    (78.980, 30.285),  # Rudraprayag
    (79.030, 30.280),
    (79.070, 30.275),  # Raturi Sera
    (79.110, 30.280),
    (79.155, 30.288),  # Gauchar
    (79.180, 30.270),
    (79.218, 30.258),  # Karnaprayag
    (79.250, 30.280),
    (79.280, 30.300),  # Langasu
    (79.310, 30.325),
    (79.330, 30.338),  # Chamoli
]

def generate_500m_segments(anchors, current_rain, rain_24h, target_segment_len_km=0.5):
    all_points = []
    # Interpolate path into smaller discrete points
    for i in range(len(anchors) - 1):
        p1, p2 = anchors[i], anchors[i+1]
        dx = (p2[0] - p1[0]) * 111 * math.cos(math.radians(p1[1]))
        dy = (p2[1] - p1[1]) * 111
        dist_km = math.sqrt(dx*dx + dy*dy)
        num_subdivisions = max(1, int(dist_km / target_segment_len_km))
        
        for step in range(num_subdivisions):
            t = step / num_subdivisions
            lon = p1[0] + t * (p2[0] - p1[0])
            lat = p1[1] + t * (p2[1] - p1[1])
            all_points.append([round(lon, 5), round(lat, 5)])
            
    all_points.append(anchors[-1])
    
    segments = []
    # Generate 500m segments with Dynamic Hazard Scoring
    for idx in range(len(all_points) - 1):
        base_vulnerability = 0.20 + (math.sin(idx * 0.15) * 0.15)
        rain_factor = (rain_24h / 150.0) + (current_rain / 20.0)
        
        hazard_score = round(base_vulnerability + rain_factor, 2)
        hazard_score = max(0.1, min(0.95, hazard_score))
        
        chainage_start = idx * 0.5
        chainage_end = (idx + 1) * 0.5
        
        segments.append({
            "segment_id": f"NH7-KM-{chainage_start:.1f}to{chainage_end:.1f}",
            "chainage": f"KM {chainage_start:.1f} - {chainage_end:.1f}",
            "hazard_score": hazard_score,
            "coords": [all_points[idx], all_points[idx+1]]
        })
        
    return segments

def run_monitoring_check():
    """Runs a single check of the weather and triggers alerts."""
    print("🌍 Background Weather Monitor Running...")
    
    try:
        # 1. Fetch Live Weather
        # Open-Meteo API allows using past_days parameter to get archived forecasts without switching endpoints.
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            "latitude=30.285&longitude=78.980"
            "&current=precipitation,rain"
            "&hourly=precipitation"
            "&past_days=1" 
            "&timezone=auto"
        )
        res = requests.get(url, timeout=5).json()
        
        current_rain = res.get("current", {}).get("precipitation", 0.0)
        hourly_precip = res.get("hourly", {}).get("precipitation", [])
        
        if len(hourly_precip) >= 24:
            rain_24h = round(sum(hourly_precip[-24:]), 1)
        else:
            rain_24h = round(sum(hourly_precip), 1)

        # 2. Generate Segments to check hazards
        micro_segments = generate_500m_segments(NH7_ANCHOR_WAYPOINTS, current_rain, rain_24h)
        high_risk_count = sum(1 for seg in micro_segments if seg["hazard_score"] >= 0.75)

        # 3. Alert Logic
        if high_risk_count > 0:
            print(f"⚠️ HIGH RISK DETECTED ({high_risk_count} zones). Dispatching Telegram alert...")
            alert_msg = (
                f"🚨 *NH-7 SAFETY ALERT* 🚨\n\n"
                f"*{high_risk_count} High-Risk landslide zones* detected between Rudraprayag and Chamoli.\n\n"
                f"🌧️ *Live Rain:* {current_rain} mm/hr\n"
                f"🌊 *24h Total:* {rain_24h} mm\n\n"
                f"⚠️ _Night travel is strictly restricted. Seek staging zones immediately._"
            )
            send_telegram_alert(alert_msg)
        else:
            print(f"✅ Coast clear. Live Rain: {current_rain}mm. High Risk Zones: {high_risk_count}.")

    except Exception as e:
        print(f"Background Monitor Error: {e}")

if __name__ == "__main__":
    run_monitoring_check()