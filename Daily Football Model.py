import random
import matplotlib.pyplot as plt
import csv
import requests
import streamlit as st
from datetime import datetime

DAYS_IN_WEEK = 7
SIMULATIONS = 10000
TARGET_ODDS = 5.00

# --- SAFEST combo ---
MIN_CONFIDENCE = 85  # Adjusted confidence
MAX_CONFIDENCE = 99
SAFE_MODE = True
SAFE_PICK_COUNT = 3
SAFE_ODDS_MIN = 1.2  # More relaxed
SAFE_ODDS_MAX = 4.0  # More relaxed

API_KEY = "fc80ba539cc7b00336a8211ccad28d44"
API_HOST = "v3.football.api-sports.io"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

st.set_page_config(page_title="5 Odds Strategy Dashboard", layout="centered")
st.title("📊 5 Odds Strategy Simulation")
st.markdown("Safest combo approach using football & basketball picks")

BASE_ODDS_URL = "https://v3.football.api-sports.io/odds"

st.header("⚽ Today's Real Smart Football Picks")

show_raw = st.checkbox("🔍 Show Raw Odds Data")

def fetch_predicted_odds():
    today = datetime.today().strftime('%Y-%m-%d')
    params = {
        "date": today,
        "timezone": "Europe/London"
    }
    response = requests.get(BASE_ODDS_URL, headers=headers, params=params)
    data = response.json()
    odds_data = data.get("response", [])

    if show_raw:
        st.subheader("📄 Raw Odds API Response")
        st.json(odds_data)

    picks = []
    combined_odds = 1.0

    for match in odds_data:
        try:
            home = match.get("teams", {}).get("home", {}).get("name", "Unknown")
            away = match.get("teams", {}).get("away", {}).get("name", "Unknown")

            if home == "Unknown" or away == "Unknown":
                continue

            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue

            bets = bookmakers[0].get("bets", [])

            for bet in bets:
                market = bet.get("name", "Unknown Market")
                for value in bet.get("values", []):
                    selection = value.get("value", "Unknown")
                    try:
                        odd = float(value.get("odd", 0))
                    except:
                        odd = 0.0

                    if SAFE_ODDS_MIN <= odd <= SAFE_ODDS_MAX:
                        confidence = random.randint(MIN_CONFIDENCE, MAX_CONFIDENCE)
                        picks.append({
                            "match": f"{home} vs {away}",
                            "market": market,
                            "selection": selection,
                            "odds": odd,
                            "confidence": confidence
                        })
                        combined_odds *= odd

                        if len(picks) == SAFE_PICK_COUNT:
                            return picks, combined_odds
        except Exception as e:
            if show_raw:
                st.error(f"Error parsing match data: {e}")
            continue

    return picks, combined_odds


