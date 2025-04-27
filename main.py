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

def get_today_date():
    return datetime.today().strftime('%Y-%m-%d')

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

        # Step 2: Skip pitchers
        if position == "P":
            return {"player": player_name, "message": "This player is a pitcher. No batting stats available."}

        # Step 3: Pull last 5 games
        game_log_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats/game/last/5?group=hitting"
        game_log_response = requests.get(game_log_url)
        game_log_data = game_log_response.json()
        game_splits = game_log_data.get("stats", [{}])[0].get("splits", [])

        last_5_games = []
        total_hits = 0
        total_at_bats = 0

        for game in game_splits:
            hits = game["stat"].get("hits", 0)
            at_bats = game["stat"].get("atBats", 0)
            date = game.get("date", "")

            try:
                game_date = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
            except:
                game_date = date

            last_5_games.append(f"{game_date}: {hits}-for-{at_bats}")
            total_hits += hits
            total_at_bats += at_bats

        if total_at_bats > 0:
            recent_avg = total_hits / total_at_bats
        else:
            recent_avg = 0.0

        # Step 4: Pull season stats
        season_stats_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting&season=2025"
        season_stats_response = requests.get(season_stats_url)
        season_stats_data = season_stats_response.json()
        splits = season_stats_data.get("stats", [{}])[0].get("splits", [])
        season_avg = 0.0

        if splits:
            season_avg_raw = splits[0]["stat"].get("avg", "0.0")
            try:
                season_avg = float(season_avg_raw)
            except:
                season_avg = 0.0

        # Step 5: Pull splits vs LHP/RHP
        split_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=statsSingleSeason&group=hitting&season=2025"
        split_response = requests.get(split_url)
        split_data = split_response.json()
        split_splits = split_data.get("stats", [{}])[0].get("splits", [])

        vs_left_avg = None
        vs_right_avg = None

        for s in split_splits:
            if s.get("split", "") == "vs Left":
                vs_left_avg = s["stat"].get("avg", "0.0")
            if s.get("split", "") == "vs Right":
                vs_right_avg = s["stat"].get("avg", "0.0")

        # Step 6: Pull today's game and opponent pitcher
        today = get_today_date()
        schedule_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
        schedule_response = requests.get(schedule_url)
        schedule_data = schedule_response.json()

        games = schedule_data.get("dates", [{}])[0].get("games", [])

        opposing_pitcher = None
        pitcher_era = None
        pitcher_hand = None

        for game in games:
            teams = game.get("teams", {})
            away = teams.get("away", {}).get("team", {}).get("name", "")
            home = teams.get("home", {}).get("team", {}).get("name", "")

            if player_info.get("currentTeam", {}).get("name", "") in [away, home]:
                probable_pitcher = teams.get("home", {}).get("probablePitcher") or teams.get("away", {}).get("probablePitcher")
                if probable_pitcher:
                    opposing_pitcher = probable_pitcher.get("fullName", "")
                    pitcher_id = probable_pitcher.get("id", "")

                    # Pull pitcher stats
                    pitcher_stats_url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=season&group=pitching&season=2025"
                    pitcher_stats_response = requests.get(pitcher_stats_url)
                    pitcher_stats_data = pitcher_stats_response.json()
                    pitcher_splits = pitcher_stats_data.get("stats", [{}])[0].get("splits", [])

                    if pitcher_splits:
                        pitcher_era = pitcher_splits[0]["stat"].get("era", "N/A")

                    pitcher_hand = probable_pitcher.get("pitchHand", {}).get("description", "")

        # Step 7: Calculate projected hit chance
        if not season_avg:
            season_avg = 0.250

        hand_adjustment = 1.0
        if pitcher_hand == "Left":
            if vs_left_avg:
                try:
                    hand_adjustment = float(vs_left_avg) / season_avg
                except:
                    pass
        elif pitcher_hand == "Right":
            if vs_right_avg:
                try:
                    hand_adjustment = float(vs_right_avg) / season_avg
                except:
                    pass

        pitcher_adjustment = 1.0
        if pitcher_era:
            try:
                era = float(pitcher_era)
                if era < 3.00:
                    pitcher_adjustment = 0.90
                elif era > 4.50:
                    pitcher_adjustment = 1.10
            except:
                pass

        base_hit_chance = recent_avg if recent_avg > 0 else season_avg
        projected_hit_chance = base_hit_chance * hand_adjustment * pitcher_adjustment
        projected_hit_chance = round(projected_hit_chance * 100, 1)

        return {
            "player": player_name,
            "recent_games": last_5_games,
            "season_batting_average": round(season_avg, 3),
            "split_vs_left": vs_left_avg,
            "split_vs_right": vs_right_avg,
            "opposing_pitcher": opposing_pitcher,
            "pitcher_era": pitcher_era,
            "pitcher_hand": pitcher_hand,
            "projected_hit_chance_today": f"{projected_hit_chance}%"
        }

    except Exception as e:
        return {"error": str(e)}
