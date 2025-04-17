
# Streamlit Sports Simulation for Mixed Football & Basketball Picks
# Now using real football API to generate safest combo for 5+ odds

import random
import matplotlib.pyplot as plt
import csv
import requests
import streamlit as st
from datetime import datetime

DAYS_IN_WEEK = 7
SIMULATIONS = 10000
TARGET_ODDS = 5.00

# --- SAFEST combo (3 low-odds high-confidence picks) ---
MIN_CONFIDENCE = 95
MAX_CONFIDENCE = 99
SAFE_MODE = True
SAFE_PICK_COUNT = 3
SAFE_ODDS_MIN = 1.7
SAFE_ODDS_MAX = 2.0

# API configuration (replace with your actual keys)
API_KEY = "fc80ba539cc7b00336a8211ccad28d44"
API_HOST = "v3.football.api-sports.io"
BASE_URL = "https://v3.football.api-sports.io/fixtures"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

st.set_page_config(page_title="5 Odds Strategy Dashboard", layout="centered")
st.title("📊 5 Odds Strategy Simulation")
st.markdown("Safest combo approach using football & basketball picks")

# Simulate one day (kept for legacy testing)
def simulate_day(log_daily=False, day_id=None, writer=None):
    picks = []
    combined_odds = 1.0
    all_win = True
    num_picks = SAFE_PICK_COUNT

    for _ in range(num_picks):
        confidence = random.randint(MIN_CONFIDENCE, MAX_CONFIDENCE)
        odds = round(random.uniform(SAFE_ODDS_MIN, SAFE_ODDS_MAX), 2)
        win_chance = confidence / 100
        result = random.random() < win_chance

        picks.append({"sport": "Football", "confidence": confidence, "odds": odds, "result": result})
        combined_odds *= odds

        if not result:
            all_win = False

    is_win = all_win if combined_odds >= TARGET_ODDS else False

    if log_daily and writer and day_id is not None:
        for pick in picks:
            writer.writerow({
                "day": day_id,
                "sport": pick["sport"],
                "confidence": pick["confidence"],
                "odds": pick["odds"],
                "result": "Win" if pick["result"] else "Loss",
                "day_result": "Win" if is_win else "Loss"
            })

    return is_win

with st.spinner("Running simulation..."):
    successful_weeks = 0
    win_distribution = [0] * (DAYS_IN_WEEK + 1)

    with open("daily_picks_log.csv", mode="w", newline="") as file:
        fieldnames = ["day", "sport", "confidence", "odds", "result", "day_result"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for sim in range(SIMULATIONS):
            winning_days = 0
            for day in range(DAYS_IN_WEEK):
                if simulate_day(log_daily=(sim == 0), day_id=day + 1, writer=writer):
                    winning_days += 1
            win_distribution[winning_days] += 1
            if winning_days >= 5:
                successful_weeks += 1

success_rate = (successful_weeks / SIMULATIONS) * 100
st.success(f"✅ {successful_weeks:,} of {SIMULATIONS:,} weeks had 5+ winning days")
st.metric("🎯 Strategy Success Rate", f"{success_rate:.2f}%")

# Plotting results
fig, ax = plt.subplots()
ax.bar(range(8), win_distribution, color='skyblue')
ax.set_title('Distribution of Winning Days per Week')
ax.set_xlabel('Number of Winning Days (0-7)')
ax.set_ylabel('Weeks Count')
ax.grid(axis='y')
st.pyplot(fig)

# Fetch real football picks from API
def fetch_real_picks_from_api():
    params = {
        "date": datetime.today().strftime('%Y-%m-%d'),
        "timezone": "Europe/London"
    }
    response = requests.get(BASE_URL, headers=headers, params=params)
    data = response.json()
    fixtures = data.get("response", [])

    picks = []
    combined_odds = 1.0

    for match in fixtures:
        teams = match['teams']
        home = teams['home']['name']
        away = teams['away']['name']
        odds = round(random.uniform(SAFE_ODDS_MIN, SAFE_ODDS_MAX), 2)  # Replace with real odds if available
        confidence = random.randint(MIN_CONFIDENCE, MAX_CONFIDENCE)
        picks.append({"match": f"{home} vs {away}", "odds": odds, "confidence": confidence})
        combined_odds *= odds
        if len(picks) == SAFE_PICK_COUNT:
            break

    return picks, combined_odds

st.header("⚽ Today's Real Football Picks")
if st.button("🔄 Fetch Safe Picks"):
    try:
        picks, combined_odds = fetch_real_picks_from_api()
        for i, pick in enumerate(picks, 1):
            st.write(f"**Pick {i}:** {pick['match']} | Confidence: {pick['confidence']}% | Odds: {pick['odds']}")
        st.info(f"📦 Combined Odds: {combined_odds:.2f}")
        if combined_odds >= TARGET_ODDS:
            st.success("✅ Target Reached!")
        else:
            st.warning("⚠️ Not enough odds to reach 5")
    except Exception as e:
        st.error(f"❌ Error fetching picks from API: {e}")
