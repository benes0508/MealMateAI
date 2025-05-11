
# services/recipe-service/main.py

import os
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# App setup
title = "Recipe Service"
app = FastAPI(title=title, version="0.1.0")

# Database URL from env
db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://recipe_user:recipe_password@postgres:5432/recipe_db"
)
engine = create_engine(db_url, future=True)

# Health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

# List all recipes
@app.get("/api/recipes/")
def list_recipes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM recipes ORDER BY id"))
            # ._mapping gives a dict-like view of the row
            recipes = [dict(row._mapping) for row in result]
        return recipes
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get one recipe by ID
@app.get("/api/recipes/{recipe_id}")
def get_recipe(recipe_id: int):
    try:
        with engine.connect() as conn:
            stmt = text("SELECT * FROM recipes WHERE id = :id")
            result = conn.execute(stmt, {"id": recipe_id})
            row = result.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return dict(row._mapping)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
