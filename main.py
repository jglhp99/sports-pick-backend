from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import requests

app = FastAPI()

# Allow all CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MLB Stats API endpoint
BASEBALL_STATS_API = "https://statsapi.mlb.com/api/v1/"

@app.get("/predict_hit")
async def predict_hit(player_name: str):
    # Search for player ID
    search_url = f"https://statsapi.mlb.com/api/v1/people/search?name={player_name}"
    search_response = requests.get(search_url)
    
    if search_response.status_code != 200:
        return {"error": "Error searching player"}

    search_data = search_response.json()
    people = search_data.get("people", [])

    if not people:
        return {"error": "Player not found"}

    player_id = people[0]["id"]

    # Get player stats for current season
    stats_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting"
    stats_response = requests.get(stats_url)

    if stats_response.status_code != 200:
        return {"error": "Error fetching stats"}

    stats_data = stats_response.json()
    splits = stats_data.get("stats", [{}])[0].get("splits", [])

    if not splits:
        return {"error": "No stats available"}

    batting_avg = splits[0]["stat"].get("avg", "N/A")
    games_played = splits[0]["stat"].get("gamesPlayed", "N/A")
    ops = splits[0]["stat"].get("ops", "N/A")

    # Fake simple stadium effect (we'll improve later)
    stadium_effect = random.choice(["Hitter friendly", "Neutral", "Pitcher friendly"])

    # Simple model: better avg and ops = higher chance
    try:
        avg_float = float(batting_avg)
        ops_float = float(ops)
        projected_hit_chance = round((avg_float * 100) + (ops_float * 10), 1)
    except:
        projected_hit_chance = round(random.uniform(50, 85), 1)

    return {
        "player": player_name,
        "recent_batting_average": batting_avg,
        "games_played": games_played,
        "stadium_effect": stadium_effect,
        "projected_hit_chance": f"{projected_hit_chance}%"
    }
