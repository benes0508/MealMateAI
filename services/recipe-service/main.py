# services/recipe-service/main.py

import os
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import pandas as pd

# App setup
title = "Recipe Service"
app = FastAPI(title=title, version="0.1.0")

# Database URL from env
db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://recipe_user:recipe_password@postgres:5432/recipe_db"
)
engine = create_engine(db_url, future=True)

# Path to the CSV file
CSV_PATH = "kaggleRecipes/recipes.csv"

# Health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}

# Get all recipes from CSV file
@app.get("/csv")
def get_csv_recipes():
    try:
        # Check if the file exists
        if not os.path.exists(CSV_PATH):
            raise HTTPException(status_code=404, detail=f"CSV file not found at {CSV_PATH}")
        
        # Read the CSV file
        df = pd.read_csv(CSV_PATH)
        
        # Convert DataFrame to list of dictionaries
        recipes = df.fillna("").to_dict(orient="records")
        
        return {"total": len(recipes), "recipes": recipes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV file: {str(e)}")

# List all recipes - removing /api/recipes prefix
@app.get("/")
def list_recipes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM recipes ORDER BY id"))
            # ._mapping gives a dict-like view of the row
            recipes = [dict(row._mapping) for row in result]
        return recipes
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Search recipes - removing /api/recipes prefix
@app.get("/search")
def search_recipes(
    query: str = "",
    dietary: Optional[List[str]] = Query(None),
    page: int = 1,
    limit: int = 12
):
    try:
        offset = (page - 1) * limit
        
        # Construct base query
        base_sql = "SELECT * FROM recipes"
        where_clauses = []
        params = {}
        
        # Add search term if provided
        if query:
            where_clauses.append("(name ILIKE :query)")
            params["query"] = f"%{query}%"
        
        # Add dietary filters if provided
        if dietary and len(dietary) > 0:
            dietary_filters = []
            for i, diet in enumerate(dietary):
                param_name = f"dietary_{i}"
                dietary_filters.append(f"dietary_tags ILIKE :{param_name}")
                params[param_name] = f"%{diet}%"
            
            if dietary_filters:
                where_clauses.append(f"({' OR '.join(dietary_filters)})")
        
        # Construct final query
        if where_clauses:
            base_sql += " WHERE " + " AND ".join(where_clauses)
        
        # Add pagination
        base_sql += " ORDER BY id LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        # Execute query
        with engine.connect() as conn:
            # Get paginated results
            result = conn.execute(text(base_sql), params)
            recipes = [dict(row._mapping) for row in result]
            
            # Count total results for pagination
            count_sql = "SELECT COUNT(*) FROM recipes"
            if where_clauses:
                count_sql += " WHERE " + " AND ".join(where_clauses)
            
            # Remove pagination params for count query
            count_params = {k: v for k, v in params.items() if k not in ["limit", "offset"]}
            count_result = conn.execute(text(count_sql), count_params)
            total = count_result.scalar()
            
        # Calculate total pages
        total_pages = (total + limit - 1) // limit
        
        return {
            "recipes": recipes,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get one recipe by ID - removing /api/recipes prefix
@app.get("/{recipe_id}")
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
