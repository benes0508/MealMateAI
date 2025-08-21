#!/usr/bin/env python3
"""
Test script to validate the RAG thinking process logging system
This script tests the logging functions without requiring database connections
"""

import logging
import json
from datetime import datetime

# Set up logging to see our output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_thinking_test.log')
    ]
)

logger = logging.getLogger(__name__)

def test_conversation_title_generation():
    """Test conversation title generation with various prompts"""
    
    def _generate_conversation_title(user_prompt: str) -> str:
        """Generate a descriptive title from user prompt"""
        prompt_lower = user_prompt.lower()
        
        # Extract key dietary terms
        dietary_terms = []
        if 'vegetarian' in prompt_lower:
            dietary_terms.append('Vegetarian')
        if 'vegan' in prompt_lower:
            dietary_terms.append('Vegan')
        if 'healthy' in prompt_lower:
            dietary_terms.append('Healthy')
        if 'protein' in prompt_lower:
            dietary_terms.append('High Protein')
        if 'low carb' in prompt_lower:
            dietary_terms.append('Low Carb')
        
        # Extract time frame
        days = 7  # default
        if '3 day' in prompt_lower:
            days = 3
        elif '5 day' in prompt_lower:
            days = 5
        elif 'week' in prompt_lower or '7 day' in prompt_lower:
            days = 7
        elif '14 day' in prompt_lower or '2 week' in prompt_lower:
            days = 14
            
        # Build title
        title_parts = []
        if dietary_terms:
            title_parts.extend(dietary_terms)
        title_parts.append(f'{days}-Day Meal Plan')
        
        return ' '.join(title_parts)
    
    logger.info("="*80)
    logger.info("🧪 TESTING RAG THINKING PROCESS LOGGING")
    logger.info("="*80)
    
    logger.info("📋 STEP 1: Testing Conversation Title Generation")
    
    test_prompts = [
        'I want healthy vegetarian meals for 7 days',
        'Give me a low carb high protein 5 day plan',
        'I need vegan breakfast ideas for a week',
        'Quick and easy meals for 3 days',
        'Healthy meal plan for 2 weeks'
    ]
    
    for prompt in test_prompts:
        title = _generate_conversation_title(prompt)
        logger.info(f"   Input: '{prompt}'")
        logger.info(f"   Generated Title: '{title}'")
        logger.info("")

def test_user_context_logging():
    """Test user context logging format"""
    
    logger.info("📋 STEP 2: Testing User Context Logging")
    
    # Mock user preferences
    user_preferences = {
        'dietary_restrictions': ['vegetarian', 'gluten-free'],
        'allergies': ['nuts', 'shellfish'],
        'cuisine_preferences': ['mediterranean', 'asian', 'mexican'],
        'cooking_preferences': ['quick', 'one-pot', 'baking'],
        'spice_tolerance': 'medium',
        'portion_preferences': 'large',
        'disliked_ingredients': ['mushrooms', 'olives']
    }
    
    user_id = 123
    user_prompt = "I want healthy vegetarian meals for 7 days"
    
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"💬 Original Prompt: '{user_prompt}'")
    logger.info(f"🎯 User Preferences Retrieved:")
    logger.info(f"   • Dietary Restrictions: {user_preferences.get('dietary_restrictions', [])}")
    logger.info(f"   • Allergies: {user_preferences.get('allergies', [])}")
    logger.info(f"   • Cuisine Preferences: {user_preferences.get('cuisine_preferences', [])}")
    logger.info(f"   • Cooking Style: {user_preferences.get('cooking_preferences', [])}")
    logger.info(f"   • Spice Tolerance: {user_preferences.get('spice_tolerance', 'unknown')}")
    logger.info(f"   • Portion Preference: {user_preferences.get('portion_preferences', 'unknown')}")
    logger.info(f"   • Disliked Ingredients: {user_preferences.get('disliked_ingredients', [])}")

def test_recipe_recommendations_logging():
    """Test recipe recommendations logging format"""
    
    logger.info("\n🤖 STEP 3: Testing Recipe Recommendations Logging")
    
    # Mock AI response from Recipe Service
    mock_ai_response = {
        "status": "success",
        "total_results": 27,
        "recommendations": [
            {
                "recipe_id": "12345",
                "title": "Mediterranean Quinoa Bowl",
                "collection": "plant-based",
                "similarity_score": 0.892,
                "summary": "Protein-rich quinoa bowl with Mediterranean flavors",
                "ingredients_preview": ["quinoa", "tomatoes", "olives", "feta"],
                "confidence": 0.85
            },
            {
                "recipe_id": "12367", 
                "title": "Fresh Garden Salad",
                "collection": "fresh-cold",
                "similarity_score": 0.845,
                "summary": "Crisp mixed greens with seasonal vegetables",
                "ingredients_preview": ["lettuce", "cucumber", "tomatoes", "carrots"],
                "confidence": 0.82
            },
            {
                "recipe_id": "12389",
                "title": "Quick Veggie Stir-fry",
                "collection": "quick-light", 
                "similarity_score": 0.823,
                "summary": "Fast and nutritious vegetable stir-fry",
                "ingredients_preview": ["broccoli", "bell peppers", "snap peas", "ginger"],
                "confidence": 0.78
            }
        ],
        "query_analysis": {
            "detected_preferences": ["healthy", "vegetarian", "quick"],
            "detected_restrictions": ["vegetarian"],
            "meal_context": "meal plan",
            "collections_searched": ["plant-based", "fresh-cold", "quick-light"],
            "processing_time_ms": 1850,
            "generated_queries": {
                "plant-based": ["healthy vegetarian meals", "nutritious plant protein"],
                "fresh-cold": ["fresh vegetable dishes", "healthy salads"],
                "quick-light": ["quick vegetarian meals", "light healthy dishes"]
            }
        }
    }
    
    # Mock conversation history
    conversation_history = [
        {
            "role": "user",
            "content": "I want healthy vegetarian meals for 7 days"
        }
    ]
    
    logger.info("🔄 Converting prompt to conversation format...")
    logger.info(f"💬 Conversation History Sent to Recipe Service:")
    logger.info(json.dumps(conversation_history, indent=4))
    
    logger.info(f"\n📤 Sending Request to Recipe Service RAG System:")
    logger.info(f"   • Max Results: 50")
    logger.info(f"   • User Preferences Included: true")
    
    logger.info(f"\n⚡ Calling Recipe Service /recommendations endpoint...")
    logger.info(f"📥 Recipe Service Response Status: {mock_ai_response.get('status', 'unknown')}")
    logger.info(f"🔢 Total Results Returned: {mock_ai_response.get('total_results', 0)}")
    
    if mock_ai_response.get("status") == "success":
        recommendations = mock_ai_response["recommendations"]
        logger.info(f"✅ SUCCESS: AI recommendations returned {len(recommendations)} recipes")
        
        # Log query analysis from Recipe Service
        if "query_analysis" in mock_ai_response:
            query_analysis = mock_ai_response["query_analysis"]
            logger.info(f"\n🔍 Recipe Service Query Analysis:")
            logger.info(f"   • Detected Preferences: {query_analysis.get('detected_preferences', [])}")
            logger.info(f"   • Detected Restrictions: {query_analysis.get('detected_restrictions', [])}")
            logger.info(f"   • Meal Context: {query_analysis.get('meal_context', 'None')}")
            logger.info(f"   • Collections Searched: {query_analysis.get('collections_searched', [])}")
            logger.info(f"   • Processing Time: {query_analysis.get('processing_time_ms', 0)}ms")
            
            if "generated_queries" in query_analysis:
                logger.info(f"\n🎯 Generated Queries by Collection:")
                for collection, queries in query_analysis["generated_queries"].items():
                    logger.info(f"     {collection}: {queries}")
        
        # Log sample of retrieved recipes
        logger.info(f"\n📋 Sample Retrieved Recipes (top 3):")
        for i, recipe in enumerate(recommendations[:3]):
            logger.info(f"   {i+1}. {recipe.get('title', 'Unknown')} (Collection: {recipe.get('collection', 'N/A')}, Score: {recipe.get('similarity_score', 0):.3f})")

def test_gemini_prompt_logging():
    """Test Gemini prompt construction and logging"""
    
    logger.info("\n🎭 STEP 4: Testing Gemini Prompt Logging")
    
    user_prompt = "I want healthy vegetarian meals for 7 days"
    
    # Mock organized collections
    collections = {
        "plant-based": [
            {
                "recipe_id": "12345",
                "recipe_name": "Mediterranean Quinoa Bowl",
                "similarity_score": 0.892,
                "ingredients": ["quinoa", "tomatoes", "olives", "feta"],
                "cuisine_type": "plant-based",
                "summary": "Protein-rich quinoa bowl with Mediterranean flavors"
            }
        ],
        "fresh-cold": [
            {
                "recipe_id": "12367",
                "recipe_name": "Fresh Garden Salad", 
                "similarity_score": 0.845,
                "ingredients": ["lettuce", "cucumber", "tomatoes"],
                "cuisine_type": "fresh-cold",
                "summary": "Crisp mixed greens with seasonal vegetables"
            }
        ]
    }
    
    logger.info("📊 Analyzing recipe collections and user context...")
    logger.info(f"📂 Recipe Collections Organized:")
    for collection, recipes in collections.items():
        avg_score = sum(r.get("similarity_score", 0) for r in recipes) / len(recipes) if recipes else 0
        logger.info(f"   • {collection}: {len(recipes)} recipes (avg score: {avg_score:.3f})")
    
    # Mock user context
    user_context = """
            USER PROFILE CONTEXT:
            - Dietary Restrictions: vegetarian, gluten-free
            - Allergies: nuts, shellfish
            - Cuisine Preferences: mediterranean, asian
            - Cooking Style: quick, one-pot
            - Spice Tolerance: medium
            - Portion Preference: large
            - Disliked Ingredients: mushrooms, olives
            """
    
    # Construct enhanced prompt
    enhanced_prompt = f"""
            Create a personalized meal plan based on this request: {user_prompt}
            {user_context}
            
            AVAILABLE AI-RECOMMENDED RECIPES (organized by collection with similarity scores):
            {json.dumps(collections, indent=2)}
            
            INSTRUCTIONS:
            1. Prioritize recipes with higher similarity_score (closer to 1.0) as they better match user intent
            2. Use recipe collections for smart meal type assignment
            3. Ensure variety across different collections and meal types
            4. Balance nutrition by including different types of recipes
            5. Create 7 days with 3 meals per day unless user specifies otherwise
            
            CRITICAL: Output ONLY the JSON object. No markdown, no extra text.
            """
    
    logger.info("✍️ Constructing Enhanced Prompt for Gemini...")
    logger.info("="*80)
    logger.info("📤 EXACT PROMPT SENT TO GEMINI:")
    logger.info("="*80)
    logger.info(enhanced_prompt)
    logger.info("="*80)
    
    # Mock Gemini response
    mock_gemini_response = """{
  "meal_plan": [
    {
      "day": 1,
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_id": 12389,
          "recipe_name": "Mediterranean Avocado Toast",
          "collection": "quick-light",
          "similarity_score": 0.798
        },
        {
          "meal_type": "lunch", 
          "recipe_id": 12345,
          "recipe_name": "Mediterranean Quinoa Bowl",
          "collection": "plant-based",
          "similarity_score": 0.892
        }
      ]
    }
  ],
  "explanation": "I've created a healthy vegetarian meal plan focusing on Mediterranean cuisine. The plan uses high-scoring recipes from plant-based and quick-light collections, avoiding nuts due to your allergy."
}"""
    
    logger.info("⏳ Sending request to Gemini API...")
    logger.info("="*80)
    logger.info("📥 EXACT RESPONSE FROM GEMINI:")
    logger.info("="*80)
    logger.info(mock_gemini_response)
    logger.info("="*80)

def test_final_quality_metrics():
    """Test final quality metrics logging"""
    
    logger.info("\n📊 STEP 5: Testing Final Quality Metrics")
    
    # Mock final meal plan data
    meal_plan = {
        "ai_enhanced": True,
        "recipes_found": 27,
        "user_prompt": "I want healthy vegetarian meals for 7 days",
        "user_preferences_applied": True,
        "avg_recipe_similarity": 0.821,
        "recipe_collections": ["plant-based", "quick-light", "fresh-cold"]
    }
    
    logger.info(f"📈 Quality Metrics:")
    logger.info(f"   • Average Recipe Similarity: {meal_plan['avg_recipe_similarity']:.3f}")
    logger.info(f"   • Collections Used: {meal_plan['recipe_collections']}")
    logger.info(f"   • User Preferences Applied: {meal_plan['user_preferences_applied']}")
    
    logger.info("="*80)
    logger.info("🎉 RAG MEAL PLAN THINKING PROCESS COMPLETE")
    logger.info("="*80)
    logger.info(f"✅ Final Meal Plan Generated:")
    logger.info(f"   • Recipes Found: {meal_plan['recipes_found']}")
    logger.info(f"   • AI Enhanced: {meal_plan['ai_enhanced']}")
    logger.info(f"   • Processing Quality: {meal_plan['avg_recipe_similarity']:.3f} average similarity")
    logger.info(f"   • Collections: {len(meal_plan['recipe_collections'])} different types")
    logger.info("="*80)

if __name__ == "__main__":
    print("🧪 Testing RAG Thinking Process Logging System")
    print("Check the output above and 'rag_thinking_test.log' file for complete logs")
    print()
    
    test_conversation_title_generation()
    test_user_context_logging()
    test_recipe_recommendations_logging() 
    test_gemini_prompt_logging()
    test_final_quality_metrics()
    
    print("\n✅ Logging system test complete!")
    print("📄 Check 'rag_thinking_test.log' for the complete log output")