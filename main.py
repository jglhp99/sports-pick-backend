from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/predict_hit")
async def predict_hit(player_name: str):
    recent_batting_avg = round(random.uniform(0.200, 0.400), 3)
    career_vs_opponent = f"{random.randint(3,10)} for {random.randint(10,20)} ({round(random.uniform(0.250, 0.500), 3)})"
    stadium_effect = random.choice(["Hitter friendly", "Neutral", "Pitcher friendly"])
    projected_hit_chance = round(random.uniform(50, 85), 1)

    return {
        "player": player_name,
        "recent_batting_average": recent_batting_avg,
        "career_vs_opponent": career_vs_opponent,
        "stadium_effect": stadium_effect,
        "projected_hit_chance": f"{projected_hit_chance}%"
    }
