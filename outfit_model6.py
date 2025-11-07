# outfit_model6.py
import csv
import random
import re
from datetime import datetime
import requests
import os

# Updated CSV file name
DATASET_FILE = "images.csv"

# Get OpenWeatherMap API key from environment variable
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
# Set WEATHER_API_KEY as an environment variable in production (recommended).

EXPECTED_COLUMNS = ["event", "season", "gender", "skin", "topwear", "bottomwear", "footwear", "accessories"]

def _normalize_link(url: str) -> str:
    """Convert Google Drive/Dropbox links into direct image links and unwrap =HYPERLINK()."""
    if not url:
        return ""
    u = url.strip()
    if u.lower().startswith("=hyperlink"):
        m = re.search(r'"(https?://[^"]+)"', u)
        if m:
            u = m.group(1)

    # Google Drive formats
    m = re.search(r'drive\.google\.com\/file\/d\/([A-Za-z0-9_-]+)', u)
    if m:
        return f"https://drive.google.com/uc?export=view&id={m.group(1)}"
    m = re.search(r'drive\.google\.com\/open\?id=([A-Za-z0-9_-]+)', u)
    if m:
        return f"https://drive.google.com/uc?export=view&id={m.group(1)}"
    m = re.search(r'drive\.google\.com\/uc\?id=([A-Za-z0-9_-]+)', u)
    if m:
        return f"https://drive.google.com/uc?export=view&id={m.group(1)}"

    # Dropbox: convert ?dl=0 → ?raw=1
    if "dropbox.com" in u and "?dl=0" in u:
        return u.replace("?dl=0", "?raw=1")

    return u

def _map_header(raw: str) -> str:
    """Map headers to canonical names."""
    if not raw:
        return raw
    h = raw.strip().lower()
    if "event" in h: return "event"
    if h in ("season", "weather"): return "season"
    if "gender" in h: return "gender"
    if "skin" in h: return "skin"
    if "top" in h: return "topwear"
    if "bottom" in h: return "bottomwear"
    if "foot" in h or "shoe" in h: return "footwear"
    if "accessor" in h: return "accessories"
    return h.replace(" ", "")

def load_dataset():
    """Load CSV and normalize values."""
    outfits = []
    try:
        with open(DATASET_FILE, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if not reader.fieldnames:
                print("⚠️ CSV missing headers.")
                return outfits

            for raw_row in reader:
                normalized = {}
                for raw_k, raw_v in raw_row.items():
                    if not raw_k:
                        continue
                    key = _map_header(raw_k)
                    value = (raw_v or "").strip()
                    if key in ["topwear", "bottomwear", "footwear", "accessories"]:
                        normalized[key] = _normalize_link(value)
                    elif key in ["event", "season", "gender", "skin"]:
                        normalized[key] = value.lower()
                    else:
                        normalized[key] = value
                outfits.append(normalized)
    except FileNotFoundError:
        print(f"❌ CSV file '{DATASET_FILE}' not found.")
    except Exception as e:
        print("❌ CSV load error:", e)
    return outfits

def get_location():
    try:
        r = requests.get("https://ipinfo.io", timeout=5)
        return r.json().get("city")
    except Exception as e:
        print("⚠️ Location error:", e)
        return None

def get_season_from_weather(city, date_str=None):
    """Map weather into summer/winter/rainy."""
    try:
        if not city:
            return "summer"

        if not date_str:
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
            data = requests.get(url, params=params, timeout=6).json()
            temp = data.get("main", {}).get("temp")
        else:
            url = f"http://api.openweathermap.org/data/2.5/forecast"
            params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
            data = requests.get(url, params=params, timeout=6).json()
            target = datetime.strptime(date_str, "%Y-%m-%d").date()
            temp = None
            for entry in data.get("list", []):
                if datetime.fromtimestamp(entry["dt"]).date() == target:
                    temp = entry["main"]["temp"]
                    break
            if temp is None and data.get("list"):
                temp = data["list"][0]["main"]["temp"]

        if temp is None:
            return "summer"
        temp = float(temp)
        if temp >= 25: return "summer"
        if temp <= 15: return "winter"
        return "rainy"
    except Exception as e:
        print("⚠️ Weather error:", e)
        return "summer"

def find_outfits(event, season, gender=None, skin=None):
    dataset = load_dataset()
    if not dataset:
        return []

    ev = (event or "").lower()
    se = (season or "").lower()
    ge = (gender or "").lower() if gender else None
    sk = (skin or "").lower() if skin else None

    try:
        matches = [r for r in dataset if r.get("event")==ev and r.get("season")==se and r.get("gender")==ge and r.get("skin")==sk]
        if matches: return matches
        matches = [r for r in dataset if r.get("event")==ev and r.get("season")==se and r.get("gender")==ge]
        if matches: return matches
        matches = [r for r in dataset if r.get("event")==ev and r.get("season")==se]
        if matches: return matches
        matches = [r for r in dataset if r.get("event")==ev]
        if matches: return matches
        return random.sample(dataset, min(3, len(dataset)))
    except Exception as e:
        print("❌ Matching error:", e)
        return []

def show_outfits(outfit_rows):
    """Generate HTML with placeholders for missing items."""
    html = ""
    for idx, row in enumerate(outfit_rows, 1):
        html += f"<h4>Outfit {idx}</h4>\n"
        html += "<div style='display:flex;gap:18px;flex-wrap:wrap;margin-bottom:24px;'>\n"
        for key in ["topwear", "bottomwear", "footwear", "accessories"]:
            link = (row.get(key) or "").strip()
            if link and link.lower() != "link":
                html += f"""
                <div style="text-align:center;">
                    <img src="{link}" style="width:200px;height:200px;object-fit:cover;border-radius:12px;border:1px solid #ddd;">
                    <div style="margin-top:6px">{key.capitalize()}</div>
                </div>
                """
            else:
                html += f"""
                <div style="text-align:center;">
                    <div style="width:200px;height:200px;background:#f7f7f7;border-radius:12px;border:1px solid #eee;display:flex;align-items:center;justify-content:center;color:#999;">
                        No {key}
                    </div>
                    <div style="margin-top:6px">{key.capitalize()}</div>
                </div>
                """
        html += "</div>\n"
    return html

def get_outfit_for_chatbot(event, date=None, gender=None, skin=None, city=None):
    try:
        used_city = city or get_location()
        season = get_season_from_weather(used_city, date)
        outfits = find_outfits(event, season, gender, skin)

        if not outfits:
            reply = f"No outfits for event='{event}', season='{season}', gender='{gender}', skin='{skin}'."
            return "<b>Sorry, no outfits found.</b>", reply

        chosen = random.sample(outfits, min(3, len(outfits)))
        html = show_outfits(chosen)
        reply = f"Showing {len(chosen)} outfit(s) for event='{event}', season='{season}', gender='{gender}', skin='{skin}', city='{used_city}'."
        return html, reply
    except Exception as e:
        print("❌ Main error:", e)
        return "<b>Error occurred.</b>", f"Error in chatbot: {e}"
