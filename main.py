from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import requests
from datetime import datetime

app = FastAPI()

# Allow all CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/predict_hit")
async def predict_hit(player_name: str):
    try:
        # Step 1: Search player
        search_url = f"https://statsapi.mlb.com/api/v1/people/search?name={player_name}"
        search_response = requests.get(search_url)
        search_data = search_response.json()

        people = search_data.get("people", [])
        if not people:
            return {"error": "Player not found"}

        player_info = people[0]
        player_id = player_info["id"]
        position = player_info.get("primaryPosition", {}).get("abbreviation", "")

        # Step 2: If pitcher, skip
        if position == "P":
            return {
                "player": player_name,
                "message": "This player is a pitcher. No batting stats available."
            }

        # Step 3: Pull last 10 games
        game_log_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats/game/last/10?group=hitting"
        game_log_response = requests.get(game_log_url)
        game_log_data = game_log_response.json()
        game_splits = game_log_data.get("stats", [{}])[0].get("splits", [])

        total_hits = 0
        total_at_bats = 0
        last_5_games = []

        for game in game_splits:
            hits = game["stat"].get("hits", 0)
            at_bats = game["stat"].get("atBats", 0)
            date = game.get("date", "")

            total_hits += hits
            total_at_bats += at_bats

            # Format date nicely
            try:
                game_date = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
            except:
                game_date = date

            last_5_games.append(f"{game_date}: {hits}-{at_bats}")

        # Step 4: Calculate real batting average
        if total_at_bats > 0:
            batting_avg = round(total_hits / total_at_bats, 3)
        else:
            batting_avg = "N/A"

        # Random stadium effect
        stadium_effect = random.choice(["Hitter friendly", "Neutral", "Pitcher friendly"])

        # Prediction based on batting average
        try:
            avg_float = float(batting_avg)
            projected_hit_chance = round(avg_float * 100 + random.uniform(5, 10), 1)
        except:
            projected_hit_chance = round(random.uniform(40, 65), 1)

        return {
            "player": player_name,
            "recent_batting_average": batting_avg,
            "total_hits": total_hits,
            "total_at_bats": total_at_bats,
            "last_5_games": last_5_games if last_5_games else ["No recent games"],
            "stadium_effect": stadium_effect,
            "projected_hit_chance": f"{projected_hit_chance}%"
        }

    except Exception as e:
        return {"error": str(e)}
