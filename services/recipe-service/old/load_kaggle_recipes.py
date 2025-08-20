#!/usr/bin/env python3
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import json

print("🚀 Starting Kaggle CSV to PostgreSQL loader...")

# Configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://recipe_user:recipe_password@postgres:5432/recipe_db"
)
CSV_PATH = "kaggleRecipes/recipes.csv"

print(f"📝 Database URL: {DATABASE_URL}")
print(f"📝 CSV Path: {CSV_PATH}")

# Check if CSV exists
if not os.path.exists(CSV_PATH):
    print(f"❌ Error: CSV file not found at {CSV_PATH}")
    exit(1)

print("🔄 Loading CSV file...")
df = pd.read_csv(CSV_PATH)
print(f"✅ Loaded {len(df)} recipes from CSV")

# Filter out recipes without required fields
print("🔄 Filtering recipes...")
df = df.dropna(subset=["recipe_name", "directions"])
print(f"✅ After filtering: {len(df)} valid recipes")

# Connect to PostgreSQL
print("🔄 Connecting to PostgreSQL...")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
print("✅ Connected to PostgreSQL")

# Clear existing data
print("🔄 Clearing existing recipes...")
cur.execute("TRUNCATE recipes RESTART IDENTITY CASCADE;")
conn.commit()
print("✅ Cleared existing recipes")

# Process and normalize records
print("🔄 Processing recipes...")
records = []

for i, row in df.iterrows():
    if i % 100 == 0:
        print(f"   Processing recipe {i+1}/{len(df)}: {row['recipe_name']}")
    
    # Basic fields
    name = row["recipe_name"]
    
    # Parse ingredients - convert from text to list
    ingredients_text = str(row.get("ingredients", ""))
    ingredients_list = [ing.strip() for ing in ingredients_text.split(",") if ing.strip()] if ingredients_text != "nan" else []
    
    # Meal type - determine from recipe name or set default
    meal_type = []
    name_lower = name.lower()
    if any(word in name_lower for word in ["breakfast", "pancake", "oatmeal", "cereal"]):
        meal_type = ["breakfast"]
    elif any(word in name_lower for word in ["lunch", "sandwich", "salad", "soup"]):
        meal_type = ["lunch"]
    elif any(word in name_lower for word in ["dinner", "steak", "chicken", "pasta"]):
        meal_type = ["dinner"]
    elif any(word in name_lower for word in ["dessert", "pie", "cake", "cookie", "crisp"]):
        meal_type = ["dessert"]
    else:
        meal_type = ["main"]
    
    # Dietary tags - extract from nutrition or ingredients
    dietary_tags = []
    nutrition_text = str(row.get("nutrition", "")).lower()
    if "vegan" in nutrition_text or "plant" in nutrition_text:
        dietary_tags.append("vegan")
    if "vegetarian" in nutrition_text or not any(meat in ingredients_text.lower() for meat in ["chicken", "beef", "pork", "fish", "turkey"]):
        dietary_tags.append("vegetarian")
    if "gluten" in nutrition_text:
        dietary_tags.append("gluten-free")
    
    # Allergens - common allergens check
    allergens = []
    ingredients_lower = ingredients_text.lower()
    if any(dairy in ingredients_lower for dairy in ["milk", "cheese", "butter", "cream"]):
        allergens.append("dairy")
    if any(nut in ingredients_lower for nut in ["peanut", "almond", "walnut", "pecan"]):
        allergens.append("nuts")
    if any(gluten in ingredients_lower for gluten in ["flour", "wheat", "bread"]):
        allergens.append("gluten")
    if "egg" in ingredients_lower:
        allergens.append("eggs")
    
    # Difficulty - estimate based on cook time and ingredient count
    difficulty = "easy"
    cook_time_str = str(row.get("cook_time", ""))
    if len(ingredients_list) > 10 or "hrs" in cook_time_str:
        difficulty = "medium"
    if len(ingredients_list) > 15:
        difficulty = "hard"
    
    # Cuisine - extract from cuisine_path
    cuisine = []
    cuisine_path = str(row.get("cuisine_path", ""))
    if cuisine_path != "nan" and "/" in cuisine_path:
        # Extract cuisine from path like "/Desserts/Fruit Desserts/Apple Dessert Recipes/"
        parts = [p.strip() for p in cuisine_path.split("/") if p.strip()]
        if parts:
            cuisine = [parts[0].lower()]
    
    # Tags - additional categorization
    tags = []
    if "quick" in name_lower or any(t in str(row.get("total_time", "")).lower() for t in ["15 min", "20 min", "30 min"]):
        tags.append("quick")
    if "healthy" in name_lower or "low fat" in nutrition_text:
        tags.append("healthy")
    if "easy" in name_lower or difficulty == "easy":
        tags.append("easy")
    
    # Additional metadata as JSON
    metadata = {
        "prep_time": str(row.get("prep_time", "")),
        "cook_time": str(row.get("cook_time", "")),
        "total_time": str(row.get("total_time", "")),
        "servings": str(row.get("servings", "")),
        "yield": str(row.get("yield", "")),
        "rating": str(row.get("rating", "")),
        "url": str(row.get("url", "")),
        "nutrition": str(row.get("nutrition", "")),
        "timing": str(row.get("timing", "")),
        "img_src": str(row.get("img_src", ""))
    }
    
    # Clean nan values
    for key, value in metadata.items():
        if value == "nan" or pd.isna(value):
            metadata[key] = ""
    
    records.append((
        name,
        ingredients_list,
        meal_type,
        dietary_tags,
        allergens,
        difficulty,
        f"kaggle_{i}.json",  # json_path
        f"kaggle_{i}.txt",   # txt_path
        cuisine,
        tags,
        str(row.get("directions", "")),  # directions
        str(row.get("img_src", "")),     # img_src
        str(row.get("prep_time", "")),   # prep_time
        str(row.get("cook_time", "")),   # cook_time
        str(row.get("servings", "")),    # servings
        str(row.get("rating", "")),      # rating
        str(row.get("nutrition", "")),   # nutrition
        str(row.get("url", ""))          # url
    ))

print(f"✅ Processed {len(records)} recipes")

# Bulk insert into PostgreSQL
if records:
    print("🔄 Inserting recipes into PostgreSQL...")
    sql = """
    INSERT INTO recipes
      (name, ingredients, meal_type, dietary_tags,
       allergens, difficulty, json_path, txt_path,
       cuisine, tags, directions, img_src, prep_time,
       cook_time, servings, rating, nutrition, url)
    VALUES %s
    """
    execute_values(cur, sql, records, page_size=100)
    conn.commit()
    print(f"✅ Inserted {len(records)} recipes into PostgreSQL")

cur.close()
conn.close()

print("🎉 Kaggle CSV successfully loaded into PostgreSQL!")