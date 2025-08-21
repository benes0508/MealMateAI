#!/usr/bin/env python3.9
"""
PostgreSQL Recipe Loader
Loads recipe data from NewDataset13k CSV into PostgreSQL database
Maps image files to recipes for frontend display
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '15432'),
    'database': os.getenv('DB_NAME', 'recipe_db'),
    'user': os.getenv('DB_USER', 'recipe_user'),
    'password': os.getenv('DB_PASSWORD', 'recipe_password')
}

# Paths
CSV_PATH = "NewDataset13k/Food Ingredients and Recipe Dataset with Image Name Mapping.csv"
IMAGES_DIR = "NewDataset13k/Food Images/Food Images/"
CLASSIFICATION_PATH = "function_classification_results/function_classified_recipes.json"

def connect_to_db():
    """Establish PostgreSQL connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info(f"✅ Connected to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

def create_tables(conn):
    """Create recipes table if it doesn't exist"""
    cursor = conn.cursor()
    
    # Create the recipes table with the schema from init.sql
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS recipes (
        id              SERIAL       PRIMARY KEY,
        name            TEXT         NOT NULL,
        ingredients     TEXT[]       NOT NULL,
        meal_type       TEXT[]       DEFAULT '{}',
        dietary_tags    TEXT[]       DEFAULT '{}',
        allergens       TEXT[]       DEFAULT '{}',
        difficulty      TEXT,
        json_path       TEXT         NOT NULL,
        txt_path        TEXT         NOT NULL,
        cuisine         TEXT[]       DEFAULT '{}',
        tags            TEXT[]       DEFAULT '{}',
        directions      TEXT,
        img_src         TEXT,
        prep_time       TEXT,
        cook_time       TEXT,
        servings        TEXT,
        rating          TEXT,
        nutrition       TEXT,
        url             TEXT,
        created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
    );
    """
    
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        logger.info("✅ Recipes table ready")
    except Exception as e:
        logger.error(f"❌ Error creating table: {e}")
        conn.rollback()
    finally:
        cursor.close()

def load_csv_data():
    """Load recipe data from CSV"""
    try:
        df = pd.read_csv(CSV_PATH)
        logger.info(f"✅ Loaded {len(df)} recipes from CSV")
        return df
    except Exception as e:
        logger.error(f"❌ Failed to load CSV: {e}")
        sys.exit(1)

def load_classification_data():
    """Load recipe classifications for additional metadata"""
    try:
        with open(CLASSIFICATION_PATH, 'r', encoding='utf-8') as f:
            classifications = json.load(f)
        logger.info(f"✅ Loaded classifications for {len(classifications)} recipes")
        return classifications
    except Exception as e:
        logger.warning(f"⚠️ Could not load classifications: {e}")
        return {}

def process_image_path(image_name):
    """Convert image name to proper path"""
    if pd.isna(image_name) or image_name == 'nan':
        return None
    
    # Add .jpg extension if not present
    if not image_name.endswith(('.jpg', '.jpeg', '.png')):
        image_name = f"{image_name}.jpg"
    
    # Check if the image file exists
    full_path = Path(IMAGES_DIR) / image_name
    
    if full_path.exists():
        # Return the path that will be served as static files
        return f"/images/{image_name}"
    else:
        return None

def process_ingredients(ingredients_str):
    """Convert ingredients string to array"""
    if pd.isna(ingredients_str):
        return []
    
    try:
        # Try to parse as JSON array first
        if ingredients_str.startswith('['):
            ingredients = eval(ingredients_str)
            if isinstance(ingredients, list):
                return ingredients
    except:
        pass
    
    # Otherwise split by comma
    return [ing.strip() for ing in str(ingredients_str).split(',') if ing.strip()]

def determine_meal_type(title, ingredients_str):
    """Determine meal type based on title and ingredients"""
    title_lower = str(title).lower()
    ingredients_lower = str(ingredients_str).lower()
    
    meal_types = []
    
    # Breakfast indicators
    if any(word in title_lower for word in ['breakfast', 'pancake', 'waffle', 'omelette', 'frittata', 'scrambled']):
        meal_types.append('breakfast')
    
    # Lunch/Dinner indicators
    if any(word in title_lower for word in ['sandwich', 'salad', 'soup', 'wrap']):
        meal_types.append('lunch')
    
    if any(word in title_lower for word in ['roast', 'grilled', 'baked', 'steak', 'chicken', 'fish']):
        meal_types.append('dinner')
    
    # Dessert indicators
    if any(word in title_lower for word in ['cake', 'cookie', 'pie', 'tart', 'dessert', 'sweet']):
        meal_types.append('dessert')
    
    # Snack indicators
    if any(word in title_lower for word in ['snack', 'dip', 'chips', 'crackers']):
        meal_types.append('snack')
    
    return meal_types if meal_types else ['lunch', 'dinner']

def determine_dietary_tags(ingredients_str):
    """Determine dietary tags based on ingredients"""
    ingredients_lower = str(ingredients_str).lower()
    dietary_tags = []
    
    # Check for vegetarian
    meat_words = ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'bacon', 'sausage', 'ham', 'fish', 'salmon', 'shrimp']
    if not any(word in ingredients_lower for word in meat_words):
        dietary_tags.append('vegetarian')
        
        # Check for vegan (no animal products)
        animal_products = ['egg', 'milk', 'cheese', 'butter', 'cream', 'yogurt', 'honey']
        if not any(word in ingredients_lower for word in animal_products):
            dietary_tags.append('vegan')
    
    # Check for gluten-free
    gluten_words = ['flour', 'bread', 'pasta', 'wheat']
    if not any(word in ingredients_lower for word in gluten_words):
        dietary_tags.append('gluten-free')
    
    return dietary_tags

def insert_recipes(conn, df, classifications):
    """Insert recipes into PostgreSQL"""
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("TRUNCATE TABLE recipes RESTART IDENTITY CASCADE")
    conn.commit()
    logger.info("🗑️ Cleared existing recipes")
    
    recipes_data = []
    skipped = 0
    
    for idx, row in df.iterrows():
        try:
            # Get recipe ID from row index
            recipe_id = str(row.get('Unnamed: 0', idx))
            
            # Get classification data if available
            classification = classifications.get(recipe_id, {})
            
            # Skip beverages as requested
            collection = classification.get('collection', '')
            if collection == 'beverages':
                skipped += 1
                continue
            
            # Process fields
            name = str(row.get('Title', 'Unknown Recipe'))
            ingredients = process_ingredients(row.get('Ingredients', ''))
            instructions = str(row.get('Instructions', ''))
            image_path = process_image_path(row.get('Image_Name'))
            
            # Determine metadata
            meal_type = determine_meal_type(name, row.get('Ingredients', ''))
            dietary_tags = determine_dietary_tags(row.get('Ingredients', ''))
            
            # Get collection as cuisine/tag
            tags = [collection] if collection else []
            cuisine = [collection] if collection else []
            
            # Create recipe tuple
            recipe_tuple = (
                name,                                    # name
                ingredients,                             # ingredients array
                meal_type,                               # meal_type array
                dietary_tags,                           # dietary_tags array
                [],                                      # allergens array (empty for now)
                'medium',                                # difficulty
                f'/data/recipe_{recipe_id}.json',       # json_path (placeholder)
                f'/data/recipe_{recipe_id}.txt',        # txt_path (placeholder)
                cuisine,                                 # cuisine array
                tags,                                    # tags array
                instructions,                            # directions
                image_path,                              # img_src
                '30 min',                                # prep_time (default)
                '45 min',                                # cook_time (default)
                '4',                                     # servings (default)
                '4.5',                                   # rating (default)
                '',                                      # nutrition
                ''                                       # url
            )
            
            recipes_data.append(recipe_tuple)
            
        except Exception as e:
            logger.warning(f"⚠️ Skipped recipe at index {idx}: {e}")
            skipped += 1
            continue
    
    # Batch insert all recipes
    if recipes_data:
        insert_sql = """
        INSERT INTO recipes (
            name, ingredients, meal_type, dietary_tags, allergens,
            difficulty, json_path, txt_path, cuisine, tags,
            directions, img_src, prep_time, cook_time, servings,
            rating, nutrition, url
        ) VALUES %s
        """
        
        try:
            execute_values(cursor, insert_sql, recipes_data)
            conn.commit()
            logger.info(f"✅ Inserted {len(recipes_data)} recipes into PostgreSQL")
            
            # Get count to verify
            cursor.execute("SELECT COUNT(*) FROM recipes")
            count = cursor.fetchone()[0]
            logger.info(f"📊 Total recipes in database: {count}")
            
        except Exception as e:
            logger.error(f"❌ Error inserting recipes: {e}")
            conn.rollback()
    
    cursor.close()
    
    if skipped > 0:
        logger.warning(f"⚠️ Skipped {skipped} recipes due to errors")

def verify_data(conn):
    """Verify data was loaded correctly"""
    cursor = conn.cursor()
    
    # Get sample recipes
    cursor.execute("""
        SELECT id, name, img_src, array_length(ingredients, 1) as ingredient_count
        FROM recipes
        WHERE img_src IS NOT NULL
        LIMIT 5
    """)
    
    logger.info("\n📋 Sample recipes with images:")
    for row in cursor.fetchall():
        logger.info(f"  ID: {row[0]}, Name: {row[1][:50]}..., Image: {row[2]}, Ingredients: {row[3]}")
    
    # Get statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_recipes,
            COUNT(img_src) as recipes_with_images,
            COUNT(DISTINCT unnest(meal_type)) as meal_types,
            COUNT(DISTINCT unnest(dietary_tags)) as dietary_tags
        FROM recipes
    """)
    
    stats = cursor.fetchone()
    logger.info(f"\n📊 Database Statistics:")
    logger.info(f"  Total Recipes: {stats[0]}")
    logger.info(f"  Recipes with Images: {stats[1]}")
    logger.info(f"  Unique Meal Types: {stats[2]}")
    logger.info(f"  Unique Dietary Tags: {stats[3]}")
    
    cursor.close()

def main():
    """Main execution function"""
    logger.info("🚀 Starting PostgreSQL Recipe Loader")
    
    # Connect to database
    conn = connect_to_db()
    
    try:
        # Create tables
        create_tables(conn)
        
        # Load data
        df = load_csv_data()
        classifications = load_classification_data()
        
        # Insert recipes
        insert_recipes(conn, df, classifications)
        
        # Verify
        verify_data(conn)
        
        logger.info("✅ Recipe loading complete!")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        conn.rollback()
    finally:
        conn.close()
        logger.info("🔌 Database connection closed")

if __name__ == "__main__":
    main()