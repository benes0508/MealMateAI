import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingsService:
    """Service for managing recipe embeddings using Google's Generative AI"""
    
    def __init__(self):
        # Get API key from environment variable
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables!")
        
        # Initialize Google Generative AI
        genai.configure(api_key=self.api_key)
        
        # Initialize embedding model
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )

    async def generate_recipe_embedding(self, recipe: Dict[str, Any]) -> List[float]:
        """
        Generate an embedding vector for a recipe
        
        Args:
            recipe: Recipe data including name, ingredients, instructions, etc.
            
        Returns:
            List of floats representing the recipe embedding
        """
        try:
            # Extract relevant recipe information
            recipe_name = recipe.get("name", "")
            ingredients = ", ".join([i.get("name", "") for i in recipe.get("ingredients", [])])
            cuisine_type = recipe.get("cuisine_type", "")
            
            # Combine recipe information into a single text
            recipe_text = f"Recipe: {recipe_name}; Ingredients: {ingredients}; Cuisine: {cuisine_type}"
            
            # Generate embedding
            embedding = await self.embedding_model.aembed_query(recipe_text)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating recipe embedding: {e}")
            # Return zeros array as fallback
            return [0.0] * 768  # Default embedding dimension

    async def store_recipe_embedding(self, db: Session, recipe: Dict[str, Any]) -> bool:
        """
        Generate and store embedding for a recipe in the database
        
        Args:
            db: Database session
            recipe: Recipe data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding
            embedding = await self.generate_recipe_embedding(recipe)
            
            # Extract ingredients as text
            ingredients_text = ", ".join([i.get("name", "") for i in recipe.get("ingredients", [])])
            
            # Store in database
            db.execute(
                text("""
                INSERT INTO recipe_embeddings (recipe_id, recipe_name, ingredients, cuisine_type, embedding)
                VALUES (:recipe_id, :recipe_name, :ingredients, :cuisine_type, :embedding)
                ON CONFLICT (recipe_id) DO UPDATE
                    SET recipe_name = :recipe_name,
                        ingredients = :ingredients,
                        cuisine_type = :cuisine_type,
                        embedding = :embedding
                """),
                {
                    "recipe_id": recipe["id"],
                    "recipe_name": recipe["name"],
                    "ingredients": ingredients_text,
                    "cuisine_type": recipe.get("cuisine_type", ""),
                    "embedding": embedding
                }
            )
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing recipe embedding: {e}")
            return False

    async def batch_store_recipe_embeddings(self, db: Session, recipes: List[Dict[str, Any]]) -> bool:
        """
        Generate and store embeddings for multiple recipes
        
        Args:
            db: Database session
            recipes: List of recipes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success_count = 0
            for recipe in recipes:
                success = await self.store_recipe_embedding(db, recipe)
                if success:
                    success_count += 1
            
            logger.info(f"Successfully stored embeddings for {success_count} out of {len(recipes)} recipes")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error batch storing recipe embeddings: {e}")
            return False

    async def find_similar_recipes(self, db: Session, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find recipes similar to a query using vector similarity search
        
        Args:
            db: Database session
            query_text: Query text to find similar recipes
            limit: Maximum number of recipes to return
            
        Returns:
            List of similar recipes
        """
        try:
            # Generate embedding for the query
            query_embedding = await self.embedding_model.aembed_query(query_text)
            
            # Perform vector similarity search
            result = db.execute(
                text("""
                SELECT recipe_id, recipe_name, ingredients, cuisine_type, 
                       1 - (embedding <=> :query_embedding) as similarity
                FROM recipe_embeddings
                ORDER BY embedding <=> :query_embedding
                LIMIT :limit
                """),
                {
                    "query_embedding": query_embedding,
                    "limit": limit
                }
            )
            
            # Convert result to list of dictionaries
            similar_recipes = []
            for row in result:
                similar_recipes.append({
                    "recipe_id": row.recipe_id,
                    "recipe_name": row.recipe_name,
                    "ingredients": row.ingredients,
                    "cuisine_type": row.cuisine_type,
                    "similarity_score": float(row.similarity)
                })
            
            return similar_recipes
            
        except Exception as e:
            logger.error(f"Error finding similar recipes: {e}")
            return []

    async def find_recipes_for_preferences(
        self, 
        db: Session, 
        preferences: Dict[str, Any], 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find recipes matching user preferences using vector similarity search
        
        Args:
            db: Database session
            preferences: User preferences including dietary restrictions, allergies, etc.
            limit: Maximum number of recipes to return
            
        Returns:
            List of matching recipes
        """
        try:
            # Build query text from preferences
            dietary_restrictions = preferences.get("dietary_restrictions", [])
            allergies = preferences.get("allergies", [])
            cuisine_preferences = preferences.get("cuisine_preferences", [])
            disliked_ingredients = preferences.get("disliked_ingredients", [])
            
            query_parts = []
            
            if dietary_restrictions:
                query_parts.append(f"Dietary restrictions: {', '.join(dietary_restrictions)}")
            
            if cuisine_preferences:
                query_parts.append(f"Preferred cuisines: {', '.join(cuisine_preferences)}")
            
            # Build a query text based on preferences
            query_text = f"Find recipes that match these preferences: {' '.join(query_parts)}"
            
            # Get similar recipes
            similar_recipes = await self.find_similar_recipes(db, query_text, limit=limit)
            
            # Filter out recipes with allergenic ingredients or disliked ingredients
            if allergies or disliked_ingredients:
                filtered_recipes = []
                for recipe in similar_recipes:
                    ingredients_list = recipe["ingredients"].lower().split(", ")
                    
                    # Check if any allergens are in the ingredients
                    has_allergen = any(allergen.lower() in " ".join(ingredients_list) for allergen in allergies)
                    
                    # Check if any disliked ingredients are in the ingredients
                    has_disliked = any(disliked.lower() in " ".join(ingredients_list) for disliked in disliked_ingredients)
                    
                    if not has_allergen and not has_disliked:
                        filtered_recipes.append(recipe)
                
                return filtered_recipes
            
            return similar_recipes
            
        except Exception as e:
            logger.error(f"Error finding recipes for preferences: {e}")
            return []