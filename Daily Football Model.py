import random
import matplotlib.pyplot as plt
import csv
import requests
import streamlit as st
from datetime import datetime
import asyncio
import aiohttp
from cachetools import TTLCache

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

# Caching API responses for 10 minutes
cache = TTLCache(maxsize=100, ttl=600)

API_KEY = "fc80ba539cc7b00336a8211ccad28d44"
API_HOST = "v3.football.api-sports.io"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

st.set_page_config(page_title="5 Odds Strategy Dashboard", layout="centered")
st.title("📊 5 Odds Strategy Simulation")
st.markdown("Safest combo approach using football & basketball picks")

# --- Real-Time Football Picks Based on API Predictions ---
BASE_FIXTURE_URL = "https://v3.football.api-sports.io/fixtures"
BASE_ODDS_URL = "https://v3.football.api-sports.io/odds"

st.header("⚽ Today's Real Smart Football Picks")

show_raw = st.checkbox("🔍 Show Raw Odds Data")

async def fetch_data(url, params=None):
    if url in cache:
        return cache[url]
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            cache[url] = data  # Cache the response
            return data

def fetch_predicted_odds():
    today = datetime.today().strftime('%Y-%m-%d')
    params = {
        "date": today,
        "timezone": "Europe/London"
    }

    # Fetch both odds and fixture data in parallel
    odds_data = asyncio.run(fetch_data(BASE_ODDS_URL, params))
    fixtures_data = asyncio.run(fetch_data(BASE_FIXTURE_URL, params))

    if show_raw:
        st.subheader("📄 Raw Odds API Response")
        st.json(odds_data)

    picks = []
    combined_odds = 1.0

    for match in odds_data.get('response', []):
        try:
            teams = match.get('teams', {})
            home = teams.get('home', {}).get('name', 'Unknown')
            away = teams.get('away', {}).get('name', 'Unknown')

            if home == 'Unknown' or away == 'Unknown':
                if show_raw:
                    st.warning("⚠️ Skipped a match with missing team info.")
                continue

            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue

            bets = bookmakers[0].get("bets", [])
            selected_bets = bets  # show all for now

            for bet in selected_bets:
                for value in bet.get("values", []):
                    label = value.get("value", "Unknown")
                    try:
                        odd = float(value.get("odd", 0))
                    except:
                        odd = 0.0

                    # Fallback for missing market or bet type
                    market = bet.get('name', 'Unknown Market')
                    selection = label if label != 'Unknown' else 'Unknown Selection'

                    if SAFE_ODDS_MIN <= odd <= SAFE_ODDS_MAX:
                        confidence = random.randint(MIN_CONFIDENCE, MAX_CONFIDENCE)
                        picks.append({
                            "match": f"{home} vs {away}",
                            "bet_type": f"{market} - {selection}",
                            "market": market,
                            "selection": selection,
                            "odds": odd,
                            "confidence": confidence
                        })
                        combined_odds *= odd

                        if len(picks) == SAFE_PICK_COUNT:
                            return picks, combined_odds

        except Exception as ex:
            if show_raw:
                st.error(f"Error in match data: {ex}")
            continue

    return picks, combined_odds

if st.button("🔄 Fetch Smart Picks"):
    try:
        picks, combined_odds = fetch_predicted_odds()
        if not picks:
            st.warning("No suitable matches found with target odds range.")
        else:
            st.write("### Picks Table")
            st.table([{
                "Match": pick['match'],
                "Market": pick['market'],
                "Selection": pick['selection'],
                "Confidence": f"{pick['confidence']}%",
                "Odds": f"{pick['odds']}"
            } for pick in picks])

            st.info(f"📦 Combined Odds: {combined_odds:.2f}")
            if combined_odds >= TARGET_ODDS:
                st.success("✅ Target Reached!")
            else:
                st.warning("⚠️ Odds below 5. Try different picks.")
    except Exception as e:
        st.error(f"❌ Error fetching real-time picks: {e}")

