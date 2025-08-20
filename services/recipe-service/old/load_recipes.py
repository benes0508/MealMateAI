#!/usr/bin/env python3
import os
import json
import glob
import psycopg2
from psycopg2.extras import execute_values

# Configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://recipe_user:recipe_password@postgres:5432/recipe_db"
)
# Recipes directory inside the container (mounted via Docker Compose)
RECIPES_DIR = os.environ.get("RECIPES_DIR", "/app/recipes")

# Connect to Postgres
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Clear existing data each run
cur.execute("TRUNCATE recipes RESTART IDENTITY CASCADE;")
conn.commit()

# Gather & normalize records
records = []
pattern = os.path.join(RECIPES_DIR, "**", "*.json")
for filepath in glob.glob(pattern, recursive=True):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle dict or list top-level JSON
    entries = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
    if not entries:
        continue

    rel_json = os.path.relpath(filepath, start=RECIPES_DIR)
    for item in entries:
        name = item.get("name") or item.get("title") or ""
        # Ingredients: expect list of dicts
        raw_ings = item.get("ingredients", [])
        ingredients = [ing.get("item", "").strip() for ing in raw_ings if isinstance(ing, dict)]

        # Meal type: ensure list
        mt = item.get("meal_type", [])
        meal_type = [mt] if isinstance(mt, str) else mt

        # Dietary tags: ensure list
        dt = item.get("dietary_tags", [])
        dietary_tags = [dt] if isinstance(dt, str) else dt

        # Allergens: ensure list
        al = item.get("allergens", [])
        allergens = [al] if isinstance(al, str) else al

        difficulty = item.get("difficulty") or ""

        # Cuisine: ensure list
        cr = item.get("cuisine", [])
        cuisine = [cr] if isinstance(cr, str) else cr

        # Extra tags: ensure list
        tg = item.get("tags", [])
        tags = [tg] if isinstance(tg, str) else tg

        json_path = rel_json
        txt_path = item.get("txt_path") or rel_json.replace(".json", ".txt")

        records.append((
            name, ingredients, meal_type, dietary_tags,
            allergens, difficulty, json_path, txt_path,
            cuisine, tags
        ))

# Bulk insert into Postgres
if records:
    sql = """
    INSERT INTO recipes
      (name, ingredients, meal_type, dietary_tags,
       allergens, difficulty, json_path, txt_path,
       cuisine, tags)
    VALUES %s
    """
    execute_values(cur, sql, records, page_size=100)
    conn.commit()

print(f"✅ Inserted {len(records)} recipe(s) from {RECIPES_DIR}")

cur.close()
conn.close()