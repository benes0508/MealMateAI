"""
Query Generation Service using Google Gemini API
"""

import os
import sys
from typing import List, Dict, Any, Optional
import time

# Security check for API keys
def check_api_security():
    """Check that API keys are properly secured"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return False
    return api_key.startswith("AIza") and len(api_key) > 35

if not check_api_security():
    print("❌ GOOGLE_API_KEY not found or invalid in environment variables")
    print("💡 Please set GOOGLE_API_KEY in your environment")
    # Don't exit, just warn - service can still work without query generation

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google Gemini API not available: {e}")
    GEMINI_AVAILABLE = False

from models import ConversationMessage, AVAILABLE_COLLECTIONS

class QueryGenerationService:
    """
    Service for generating optimized search queries using Gemini API
    """
    
    def __init__(self):
        self.genai_client = None
        self._initialized = False
        
        if GEMINI_AVAILABLE:
            try:
                self.genai_client = genai.Client()
                self._initialized = True
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
                self._initialized = False
    
    def is_available(self) -> bool:
        """Check if query generation service is available"""
        return self._initialized and GEMINI_AVAILABLE
    
    async def analyze_conversation_context(
        self,
        conversation_history: List[ConversationMessage]
    ) -> Dict[str, Any]:
        """Analyze conversation to extract food preferences and context"""
        if not self.is_available():
            return self._fallback_analysis(conversation_history)
        
        # Prepare conversation text for analysis
        conversation_text = self._format_conversation(conversation_history)
        
        analysis_prompt = f"""
        Analyze the following conversation to extract food-related information:

        {conversation_text}

        Please provide a JSON response with:
        - detected_preferences: list of food preferences mentioned
        - detected_restrictions: list of dietary restrictions (vegan, gluten-free, etc.)
        - meal_context: type of meal or eating occasion (breakfast, lunch, dinner, snack, etc.)
        - cooking_preferences: cooking methods or difficulty preferences
        - ingredients_mentioned: specific ingredients mentioned
        - cuisine_preferences: cuisine types mentioned

        Return only valid JSON, no additional text.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[analysis_prompt]
            )
            
            response_text = ""
            if hasattr(response, "text"):
                response_text = response.text
            else:
                candidates = getattr(response, "candidates", [])
                if candidates:
                    content = getattr(candidates[0], "content", None)
                    if content and hasattr(content, "text"):
                        response_text = content.text
            
            if response_text:
                import json
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    
            return self._fallback_analysis(conversation_history)
            
        except Exception as e:
            print(f"Error analyzing conversation context: {e}")
            return self._fallback_analysis(conversation_history)
    
    async def generate_collection_queries(
        self,
        conversation_history: List[ConversationMessage],
        context_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """Generate 2 optimized queries per collection based on conversation context"""
        
        if not self.is_available():
            return self._fallback_queries(conversation_history)
        
        if not context_analysis:
            context_analysis = await self.analyze_conversation_context(conversation_history)
        
        # Prepare context summary
        context_summary = self._create_context_summary(context_analysis, conversation_history)
        
        query_prompt = f"""
        Based on this food conversation context:
        {context_summary}
        
        Generate 2 optimized search queries for each of these recipe collections:
        
        Collections:
        - baked-breads: Baking-focused dishes (breads, pastries, baked goods)
        - quick-light: Fast preparation and light meals (salads, wraps, quick dishes)
        - protein-mains: Meat, poultry, seafood main dishes
        - comfort-cooked: Slow-cooked and braised dishes (stews, braises, comfort food)
        - desserts-sweets: All sweet treats and desserts
        - breakfast-morning: Morning-specific foods (breakfast items)
        - plant-based: Vegetarian and vegan dishes
        - fresh-cold: Salads and raw preparations (fresh, uncooked dishes)
        
        For each collection, create 2 specific, targeted search queries that would find relevant recipes based on the conversation context. Make queries specific to what the user might want from each category.
        
        Return as JSON format:
        {{
          "baked-breads": ["query1", "query2"],
          "quick-light": ["query1", "query2"],
          ...
        }}
        
        Return only valid JSON, no additional text.
        """
        
        try:
            response = self.genai_client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=[query_prompt]
            )
            
            response_text = ""
            if hasattr(response, "text"):
                response_text = response.text
            else:
                candidates = getattr(response, "candidates", [])
                if candidates:
                    content = getattr(candidates[0], "content", None)
                    if content and hasattr(content, "text"):
                        response_text = content.text
            
            if response_text:
                import json
                try:
                    queries = json.loads(response_text)
                    # Validate structure
                    if isinstance(queries, dict):
                        validated_queries = {}
                        for collection in AVAILABLE_COLLECTIONS.keys():
                            if collection in queries and isinstance(queries[collection], list):
                                validated_queries[collection] = queries[collection][:2]  # Limit to 2 queries
                            else:
                                validated_queries[collection] = self._fallback_collection_queries(collection)
                        return validated_queries
                except json.JSONDecodeError:
                    pass
            
            return self._fallback_queries(conversation_history)
            
        except Exception as e:
            print(f"Error generating collection queries: {e}")
            return self._fallback_queries(conversation_history)
    
    def _format_conversation(self, conversation_history: List[ConversationMessage]) -> str:
        """Format conversation history for analysis"""
        formatted_lines = []
        for msg in conversation_history[-10:]:  # Use last 10 messages
            role = msg.role.capitalize()
            content = msg.content[:300]  # Limit content length
            formatted_lines.append(f"{role}: {content}")
        
        return "\n".join(formatted_lines)
    
    def _create_context_summary(
        self,
        analysis: Dict[str, Any],
        conversation_history: List[ConversationMessage]
    ) -> str:
        """Create a summary of the conversation context"""
        summary_parts = []
        
        if analysis.get("detected_preferences"):
            summary_parts.append(f"Food preferences: {', '.join(analysis['detected_preferences'])}")
        
        if analysis.get("detected_restrictions"):
            summary_parts.append(f"Dietary restrictions: {', '.join(analysis['detected_restrictions'])}")
        
        if analysis.get("meal_context"):
            summary_parts.append(f"Meal context: {analysis['meal_context']}")
        
        if analysis.get("cooking_preferences"):
            summary_parts.append(f"Cooking preferences: {', '.join(analysis['cooking_preferences'])}")
        
        if analysis.get("ingredients_mentioned"):
            summary_parts.append(f"Ingredients mentioned: {', '.join(analysis['ingredients_mentioned'])}")
        
        if analysis.get("cuisine_preferences"):
            summary_parts.append(f"Cuisine preferences: {', '.join(analysis['cuisine_preferences'])}")
        
        # Add recent conversation context
        recent_messages = conversation_history[-3:]  # Last 3 messages
        if recent_messages:
            summary_parts.append("Recent conversation:")
            for msg in recent_messages:
                summary_parts.append(f"- {msg.role}: {msg.content[:100]}...")
        
        return "\n".join(summary_parts)
    
    def _fallback_analysis(self, conversation_history: List[ConversationMessage]) -> Dict[str, Any]:
        """Fallback analysis when Gemini is not available"""
        # Simple keyword-based analysis
        text = " ".join([msg.content.lower() for msg in conversation_history[-5:]])
        
        detected_preferences = []
        detected_restrictions = []
        meal_context = None
        
        # Simple keyword detection
        preference_keywords = {
            "spicy": ["spicy", "hot", "pepper", "chili"],
            "sweet": ["sweet", "dessert", "candy", "sugar"],
            "healthy": ["healthy", "nutritious", "diet", "wellness"],
            "comfort": ["comfort", "cozy", "warm", "hearty"]
        }
        
        for pref, keywords in preference_keywords.items():
            if any(keyword in text for keyword in keywords):
                detected_preferences.append(pref)
        
        # Dietary restrictions
        restriction_keywords = {
            "vegan": ["vegan", "plant-based"],
            "vegetarian": ["vegetarian", "veggie"],
            "gluten-free": ["gluten-free", "gluten free", "celiac"],
            "dairy-free": ["dairy-free", "lactose", "no dairy"]
        }
        
        for restriction, keywords in restriction_keywords.items():
            if any(keyword in text for keyword in keywords):
                detected_restrictions.append(restriction)
        
        # Meal context
        meal_keywords = {
            "breakfast": ["breakfast", "morning", "brunch"],
            "lunch": ["lunch", "afternoon"],
            "dinner": ["dinner", "evening", "supper"],
            "snack": ["snack", "quick", "light"]
        }
        
        for meal, keywords in meal_keywords.items():
            if any(keyword in text for keyword in keywords):
                meal_context = meal
                break
        
        return {
            "detected_preferences": detected_preferences,
            "detected_restrictions": detected_restrictions,
            "meal_context": meal_context,
            "cooking_preferences": [],
            "ingredients_mentioned": [],
            "cuisine_preferences": []
        }
    
    def _fallback_queries(self, conversation_history: List[ConversationMessage]) -> Dict[str, List[str]]:
        """Generate fallback queries when Gemini is not available"""
        # Extract key terms from conversation
        text = " ".join([msg.content.lower() for msg in conversation_history[-3:]])
        
        # Default queries for each collection
        base_queries = {
            "baked-breads": ["fresh bread recipes", "homemade pastries"],
            "quick-light": ["quick meal ideas", "light lunch recipes"],
            "protein-mains": ["main course dishes", "protein-rich meals"],
            "comfort-cooked": ["comfort food recipes", "hearty stews"],
            "desserts-sweets": ["sweet treats", "dessert recipes"],
            "breakfast-morning": ["breakfast ideas", "morning meals"],
            "plant-based": ["vegetarian recipes", "plant-based meals"],
            "fresh-cold": ["fresh salads", "cold dishes"]
        }
        
        # Try to customize based on keywords found
        if "healthy" in text or "diet" in text:
            base_queries["quick-light"] = ["healthy quick meals", "nutritious light dishes"]
            base_queries["fresh-cold"] = ["healthy salads", "fresh vegetable dishes"]
        
        if "sweet" in text or "dessert" in text:
            base_queries["desserts-sweets"] = ["sweet desserts", "indulgent treats"]
        
        return base_queries
    
    def _fallback_collection_queries(self, collection_name: str) -> List[str]:
        """Generate fallback queries for a specific collection"""
        fallback_map = {
            "baked-breads": ["bread recipes", "baked goods"],
            "quick-light": ["quick meals", "light dishes"],
            "protein-mains": ["main dishes", "protein meals"],
            "comfort-cooked": ["comfort food", "slow cooked"],
            "desserts-sweets": ["desserts", "sweet treats"],
            "breakfast-morning": ["breakfast", "morning food"],
            "plant-based": ["vegetarian", "vegan dishes"],
            "fresh-cold": ["salads", "fresh dishes"]
        }
        
        return fallback_map.get(collection_name, ["recipes", "food"])