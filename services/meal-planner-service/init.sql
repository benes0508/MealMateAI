-- Create database if it doesn't exist
CREATE DATABASE meal_planner_db;

-- Connect to the database
\c meal_planner_db

-- Create user with password
CREATE USER meal_planner_user WITH PASSWORD 'meal_planner_password';

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON DATABASE meal_planner_db TO meal_planner_user;

-- Create pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables
CREATE TABLE IF NOT EXISTS meal_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    plan_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    days INTEGER NOT NULL,
    meals_per_day INTEGER NOT NULL,
    plan_data TEXT NOT NULL,
    plan_explanation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meal_plan_recipes (
    id SERIAL PRIMARY KEY,
    meal_plan_id INTEGER REFERENCES meal_plans(id) ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL,
    day INTEGER NOT NULL,
    meal_type VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_preferences_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    dietary_restrictions TEXT,
    allergies TEXT,
    cuisine_preferences TEXT,
    disliked_ingredients TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create recipe embeddings table for vector search
CREATE TABLE IF NOT EXISTS recipe_embeddings (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL UNIQUE,
    recipe_name TEXT NOT NULL,
    ingredients TEXT NOT NULL,
    cuisine_type TEXT,
    embedding vector(768),  -- Dimension size depends on the embedding model
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_id ON meal_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_recipes_meal_plan_id ON meal_plan_recipes(meal_plan_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_cache_user_id ON user_preferences_cache(user_id);
CREATE INDEX IF NOT EXISTS idx_recipe_embeddings_recipe_id ON recipe_embeddings(recipe_id);

-- Create vector index for fast similarity search
CREATE INDEX IF NOT EXISTS recipe_embeddings_vector_idx ON recipe_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Grant privileges on all tables to the user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO meal_planner_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO meal_planner_user;