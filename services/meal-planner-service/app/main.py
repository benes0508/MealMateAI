#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import json
from google import genai

# ─── CONFIG ────────────────────────────────────────────────────────────
USER_SERVICE_URL   = os.getenv("USER_SERVICE_URL",   "http://user-service:8000")
RECIPE_SERVICE_URL = os.getenv("RECIPE_SERVICE_URL", "http://recipe-service:8001")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY",     "")
GEMINI_MODEL       = os.getenv("GEMINI_MODEL",       "gemini-2.5-flash")

# Initialize Google GenAI client
genai_client = genai.Client(api_key=GEMINI_API_KEY)

title = "Meal Planner Service"
app = FastAPI(title=title, version="0.1.0")

# ─── HELPERS ───────────────────────────────────────────────────────────
def fetch_user(user_id: str):
    resp = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
    resp.raise_for_status()
    return resp.json()

def search_recipes(prompt: str, dietary_tags: list):
    # pass dietary_tags as a comma-separated filter param
    params = {"query": prompt, "dietary_tags": ",".join(dietary_tags)}
    resp = requests.get(f"{RECIPE_SERVICE_URL}/search", params=params)
    resp.raise_for_status()
    return resp.json()

def call_gemini(system_prompt: str, user_prompt: str):
    contents = system_prompt + "\n\n" + user_prompt
    response = genai_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents
    )
    return response.text

# ─── MODELS ────────────────────────────────────────────────────────────
class MealPlanRequest(BaseModel):
    user_id: str
    prompt: str

# ─── ENDPOINTS ─────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/plan-meal/")
def plan_meal(req: MealPlanRequest):
    user_id = req.user_id
    prompt = req.prompt

    try:
        # 1) get user info
        user = fetch_user(user_id)
        dietary_tags = user.get("dietary_tags", [])
        allergens    = user.get("allergens", [])

        # 2) get recipe suggestions
        recipes = search_recipes(prompt, dietary_tags)

        # 3) build prompts for Gemini
        system = (
            "You are a meal-planning assistant. Respect user dietary restrictions "
            "and allergens. If a recipe conflicts with allergies or tags, adjust it "
            "accordingly (e.g., remove cheese for kosher)."
        )
        user_msg = (
            f"User dietary tags: {', '.join(dietary_tags)}\n"
            f"User allergens: {', '.join(allergens)}\n\n"
            f"User request: {prompt}\n\n"
            f"Recipe candidates:\n{json.dumps(recipes, indent=2)}\n\n"
            "Please propose a 3-day meal plan and modify any recipes to comply."
        )

        # 4) call Gemini
        plan = call_gemini(system, user_msg)

        return {
            "user": user_id,
            "plan": plan,
            "recipes_used": recipes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))