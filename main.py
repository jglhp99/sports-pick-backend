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

    # Get season stats
    stats_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting"
    stats_response = requests.get(stats_url)

    # Get last 5 games
    game_log_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats/game/last/5?group=hitting"
    game_log_response = requests.get(game_log_url)

    if stats_response.status_code != 200 or game_log_response.status_code != 200:
        return {"error": "Error fetching stats"}

    stats_data = stats_response.json()
    splits = stats_data.get("stats", [{}])[0].get("splits", [])
    
    game_log_data = game_log_response.json()
    game_splits = game_log_data.get("stats", [{}])[0].get("splits", [])

    batting_avg = splits[0]["stat"].get("avg", "N/A") if splits else "N/A"
    games_played = splits[0]["stat"].get("gamesPlayed", "N/A") if splits else "N/A"

    # Last 5 games results WITH dates
    last_5_games = []
    for game in game_splits:
        date = game.get("date", "")
        hits = game["stat"].get("hits", 0)
        at_bats = game["stat"].get("atBats", 0)

        # Format date
        try:
            game_date = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
        except:
            game_date = date

        last_5_games.append(f"{game_date}: {hits}-{at_bats}")

    # Fake simple stadium effect (still random for now)
    stadium_effect = random.choice(["Hitter friendly", "Neutral", "Pitcher friendly"])

    # Simple prediction based on batting average
    try:
        avg_float = float(batting_avg)
        projected_hit_chance = round(avg_float * 100 + random.uniform(5, 15), 1)
    except:
        projected_hit_chance = round(random.uniform(50, 85), 1)

    return {
        "player": player_name,
        "recent_batting_average": batting_avg,
        "games_played": games_played,
        "last_5_games": last_5_games,
        "stadium_effect": stadium_effect,
        "projected_hit_chance": f"{projected_hit_chance}%"
    }
