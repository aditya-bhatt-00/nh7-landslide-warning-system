import requests
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