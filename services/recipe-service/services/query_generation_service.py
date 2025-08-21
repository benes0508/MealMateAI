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
        return False, "No API key found"
    if not api_key.startswith("AIza"):
        return False, "API key format invalid"
    if len(api_key) < 35:
        return False, "API key too short"
    return True, "Valid API key format"

def log_startup_status():
    """Log detailed startup status for debugging"""
    print("🚀 Initializing Query Generation Service...")
    
    # Check API key
    api_valid, api_reason = check_api_security()
    if api_valid:
        # Mask the API key for security
        api_key = os.getenv("GOOGLE_API_KEY", "")
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        print(f"✅ GOOGLE_API_KEY: {masked_key} ({api_reason})")
    else:
        print(f"❌ GOOGLE_API_KEY: {api_reason}")
        print("💡 To enable Gemini query generation, set GOOGLE_API_KEY environment variable")
        print("💡 Format: export GOOGLE_API_KEY='AIzaS...'")
    
    return api_valid

# Log startup status
GOOGLE_API_KEY_VALID = log_startup_status()

try:
    from google import genai
    GEMINI_AVAILABLE = True
    print("✅ Google Gemini library imported successfully")
except ImportError as e:
    print(f"❌ Google Gemini library import failed: {e}")
    print("💡 Install with: pip install google-generativeai")
    GEMINI_AVAILABLE = False

from models import ConversationMessage, AVAILABLE_COLLECTIONS

class QueryGenerationService:
    """
    Service for generating optimized search queries using Gemini API
    """
    
    def __init__(self):
        self.genai_client = None
        self._initialized = False
        
        print("🔧 Setting up Gemini client...")
        
        if not GEMINI_AVAILABLE:
            print("❌ Gemini library not available - query generation will use fallbacks")
            return
        
        if not GOOGLE_API_KEY_VALID:
            print("❌ Invalid API key - query generation will use fallbacks")
            return
        
        try:
            print("🔗 Connecting to Gemini API...")
            self.genai_client = genai.Client()
            self._initialized = True
            print("✅ Gemini client initialized successfully")
            print("🎯 Smart query generation enabled!")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini client: {e}")
            print("⚠️ Query generation will use fallbacks")
            self._initialized = False
    
    def is_available(self) -> bool:
        """Check if query generation service is available"""
        return self._initialized and GEMINI_AVAILABLE and GOOGLE_API_KEY_VALID
    
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
        
        print("🎯 Generating collection-specific queries...")
        print(f"🔍 Gemini available: {self.is_available()}")
        
        if not self.is_available():
            print("⚠️ Gemini not available, using fallback queries")
            print("💡 Reason: API key missing or Gemini client initialization failed")
            return self._fallback_queries(conversation_history)
        
        if not context_analysis:
            print("📋 Analyzing conversation context...")
            context_analysis = await self.analyze_conversation_context(conversation_history)
        
        print(f"🎯 Extracted context:")
        print(f"   • Detected Preferences: {context_analysis.get('detected_preferences', [])}")
        print(f"   • Detected Restrictions: {context_analysis.get('detected_restrictions', [])}")
        print(f"   • Meal Context: {context_analysis.get('meal_context', 'None')}")
        print(f"   • Cooking Preferences: {context_analysis.get('cooking_preferences', [])}")
        print(f"   • Ingredients Mentioned: {context_analysis.get('ingredients_mentioned', [])}")
        print(f"   • Cuisine Preferences: {context_analysis.get('cuisine_preferences', [])}")
        
        # Extract the actual user message for better context
        user_request = ""
        if conversation_history:
            user_request = conversation_history[-1].content  # Get the latest user message
        
        print(f"📝 User Request: '{user_request}'")
        
        # Prepare context summary
        context_summary = self._create_context_summary(context_analysis, conversation_history)
        
        query_prompt = f"""
        IMPORTANT: The user specifically requested: "{user_request}"
        
        Context analysis:
        {context_summary}
        
        Generate 2 highly specific search queries for each recipe collection that directly address the user's request. 
        
        User wants: {user_request}
        
        For EACH collection below, create 2 targeted queries that incorporate the user's specific requirements:
        
        Collections:
        - baked-breads: Baking-focused dishes (breads, pastries, baked goods)
        - quick-light: Fast preparation and light meals (salads, wraps, quick dishes)  
        - protein-mains: Meat, poultry, seafood main dishes
        - comfort-cooked: Slow-cooked and braised dishes (stews, braises, comfort food)
        - desserts-sweets: All sweet treats and desserts
        - breakfast-morning: Morning-specific foods (breakfast items)
        - plant-based: Vegetarian and vegan dishes
        - fresh-cold: Salads and raw preparations (fresh, uncooked dishes)
        
        CRITICAL: If the user said "no salads", do NOT include salad queries.
        CRITICAL: If the user wants "high protein", include "high protein" in relevant queries.
        CRITICAL: If the user wants "low carbs", include "low carb" in relevant queries.
        CRITICAL: If the user wants "easy to cook", include "easy" or "quick" or "simple" in queries.
        
        Examples based on user request "{user_request}":
        - For protein-mains: ["easy high protein chicken recipes", "simple low carb beef dishes"]
        - For quick-light: ["quick high protein meals", "easy low carb lunch ideas"]
        - For breakfast-morning: ["high protein low carb breakfast", "easy morning protein meals"]
        
        Return as JSON format:
        {{
          "baked-breads": ["query1", "query2"],
          "quick-light": ["query1", "query2"],
          "protein-mains": ["query1", "query2"],
          "comfort-cooked": ["query1", "query2"],
          "desserts-sweets": ["query1", "query2"],
          "breakfast-morning": ["query1", "query2"],
          "plant-based": ["query1", "query2"],
          "fresh-cold": ["query1", "query2"]
        }}
        
        Return ONLY valid JSON, no markdown, no additional text.
        """
        
        print("📝 Constructing enhanced prompt for Gemini...")
        print("="*80)
        print("📤 EXACT PROMPT SENT TO GEMINI:")
        print("="*80)
        print(query_prompt)
        print("="*80)
        
        try:
            print("⏳ Sending request to Gemini API...")
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
            
            print("="*80)
            print("📥 EXACT RESPONSE FROM GEMINI:")
            print("="*80)
            print(response_text)
            print("="*80)
            
            if response_text:
                import json
                try:
                    print("🔄 Parsing Gemini response...")
                    queries = json.loads(response_text)
                    # Validate structure
                    if isinstance(queries, dict):
                        validated_queries = {}
                        successful_collections = 0
                        for collection in AVAILABLE_COLLECTIONS.keys():
                            if collection in queries and isinstance(queries[collection], list):
                                validated_queries[collection] = queries[collection][:2]  # Limit to 2 queries
                                successful_collections += 1
                            else:
                                print(f"⚠️ Collection '{collection}' missing or invalid in Gemini response, using fallback")
                                validated_queries[collection] = self._fallback_collection_queries(collection)
                        
                        print(f"✅ Using Gemini-generated queries ({successful_collections}/{len(AVAILABLE_COLLECTIONS)} collections successful)")
                        return validated_queries
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse Gemini JSON response: {e}")
                    print("⚠️ Falling back to default queries")
            else:
                print("❌ Empty response from Gemini")
                print("⚠️ Falling back to default queries")
            
            return self._fallback_queries(conversation_history)
            
        except Exception as e:
            print(f"❌ Error generating collection queries with Gemini: {e}")
            print("⚠️ Falling back to default queries due to API error")
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
        print("🔄 Generating fallback queries with keyword-based customization...")
        
        # Extract key terms from conversation
        text = " ".join([msg.content.lower() for msg in conversation_history[-3:]])
        print(f"📝 Analyzing text for keywords: '{text[:100]}...'")
        
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
        customizations = []
        if "healthy" in text or "diet" in text:
            base_queries["quick-light"] = ["healthy quick meals", "nutritious light dishes"]
            base_queries["fresh-cold"] = ["healthy salads", "fresh vegetable dishes"]
            customizations.append("healthy")
        
        if "sweet" in text or "dessert" in text:
            base_queries["desserts-sweets"] = ["sweet desserts", "indulgent treats"]
            customizations.append("sweet/dessert")
        
        if customizations:
            print(f"🎯 Applied keyword customizations: {customizations}")
        else:
            print("📋 Using default fallback queries (no specific keywords detected)")
        
        print("⚠️ Using fallback queries instead of Gemini-generated queries")
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