# RAG Thinking Process Logging System

## Overview
Comprehensive logging system to track the entire "thinking" process of our RAG-powered meal planning system. Shows exactly what data flows through each stage and what prompts are sent to AI services.

## What Gets Logged

### 🧠 Complete Thinking Process
The logs show the AI system's complete reasoning process with detailed stage-by-stage analysis:

1. **User Context Gathering** - What we know about the user
2. **Meal Plan History Analysis** - Previous preferences and patterns  
3. **AI Recipe Recommendations** - RAG system queries and results
4. **Gemini Meal Plan Generation** - Exact prompts and responses
5. **Quality Analysis** - Final metrics and validation

## Log Structure

### Stage 1: User Context Analysis
```
================================================================================
🧠 STARTING RAG MEAL PLAN THINKING PROCESS
================================================================================

📋 STEP 1: Gathering User Context
👤 User ID: 123
💬 Original Prompt: 'I want healthy vegetarian meals for 7 days'
🎯 User Preferences Retrieved:
   • Dietary Restrictions: ['vegetarian']
   • Allergies: ['nuts']
   • Cuisine Preferences: ['mediterranean', 'asian']
   • Cooking Style: ['quick', 'one-pot']
   • Spice Tolerance: medium
   • Portion Preference: medium
```

### Stage 2: Meal Plan History
```
📚 STEP 2: Analyzing Meal Plan History
🗂️ Recent Meal Plans (last 3): [45, 42, 38]
   Plan 1: Vegetarian Mediterranean 7-Day Plan (ID: 45)
   Plan 2: Quick Healthy 5-Day Plan (ID: 42)  
   Plan 3: Asian Fusion 7-Day Plan (ID: 38)
```

### Stage 3: Recipe Service RAG Analysis
```
🤖 STEP 3: AI-Powered Recipe Recommendations
🔄 Converting prompt to conversation format...
💬 Conversation History Sent to Recipe Service:
[
    {
        "role": "user",
        "content": "I want healthy vegetarian meals for 7 days"
    }
]

📤 Sending Request to Recipe Service RAG System:
   • Max Results: 50
   • User Preferences Included: true
   • Preferences Data: {
       "dietary_restrictions": ["vegetarian"],
       "allergies": ["nuts"],
       ...
     }

⚡ Calling Recipe Service /recommendations endpoint...
📥 Recipe Service Response Status: success
🔢 Total Results Returned: 27

✅ SUCCESS: AI recommendations returned 27 recipes

🔍 Recipe Service Query Analysis:
   • Detected Preferences: ['healthy', 'vegetarian', 'quick']
   • Detected Restrictions: ['vegetarian']  
   • Meal Context: meal plan
   • Collections Searched: ['plant-based', 'fresh-cold', 'quick-light']
   • Processing Time: 1850ms

🎯 Generated Queries by Collection:
     plant-based: ["healthy vegetarian meals", "nutritious plant protein"]
     fresh-cold: ["fresh vegetable dishes", "healthy salads"]
     quick-light: ["quick vegetarian meals", "light healthy dishes"]

📋 Sample Retrieved Recipes (top 5):
   1. Mediterranean Quinoa Bowl (Collection: plant-based, Score: 0.892)
   2. Fresh Garden Salad (Collection: fresh-cold, Score: 0.845)
   3. Quick Veggie Stir-fry (Collection: quick-light, Score: 0.823)
   4. Lentil Power Bowl (Collection: plant-based, Score: 0.812)
   5. Avocado Toast Deluxe (Collection: quick-light, Score: 0.798)
```

### Stage 4: Gemini Prompt Analysis
```
🎭 STEP 4: Gemini Meal Plan Generation
📝 Input Data Analysis:
   • User Prompt: 'I want healthy vegetarian meals for 7 days'
   • Retrieved Recipes Count: 27
   • AI-Enhanced Recipes: true

📊 Analyzing recipe collections and user context...
📂 Recipe Collections Organized:
   • plant-based: 12 recipes (avg score: 0.834)
   • fresh-cold: 8 recipes (avg score: 0.792)  
   • quick-light: 7 recipes (avg score: 0.756)

👤 User Preferences Available in Recipe Data: true
🔍 Extracting User Context for Prompt:
   • Dietary Restrictions: ['vegetarian']
   • Allergies: ['nuts']
   • Cuisine Preferences: ['mediterranean', 'asian']
   • Cooking Style: ['quick', 'one-pot']
   • Spice Tolerance: medium

✍️ Constructing Enhanced Prompt for Gemini...
```

### Stage 5: Exact Gemini Communication
```
================================================================================
📤 EXACT PROMPT SENT TO GEMINI:
================================================================================

Create a personalized meal plan based on this request: I want healthy vegetarian meals for 7 days

USER PROFILE CONTEXT:
- Dietary Restrictions: vegetarian
- Allergies: nuts
- Cuisine Preferences: mediterranean, asian
- Cooking Style: quick, one-pot
- Spice Tolerance: medium
- Portion Preference: medium
- Disliked Ingredients: mushrooms

AVAILABLE AI-RECOMMENDED RECIPES (organized by collection with similarity scores):
{
  "plant-based": [
    {
      "recipe_id": "12345",
      "recipe_name": "Mediterranean Quinoa Bowl",
      "similarity_score": 0.892,
      "ingredients": ["quinoa", "tomatoes", "olives", "feta"],
      "cuisine_type": "plant-based",
      "summary": "Protein-rich quinoa bowl with Mediterranean flavors..."
    },
    // ... more recipes
  ],
  "fresh-cold": [
    // ... recipes
  ]
}

INSTRUCTIONS:
1. Prioritize recipes with higher similarity_score (closer to 1.0) as they better match user intent
2. Use recipe collections for smart meal type assignment:
   - breakfast-morning: breakfast meals
   - desserts-sweets: desserts or sweet snacks  
   - protein-mains: lunch/dinner main courses
   - quick-light: light meals, snacks, quick options
   - fresh-cold: salads, cold preparations
   - baked-breads: baked goods, bread-based meals
   - comfort-cooked: hearty dinner meals
   - plant-based: vegetarian/vegan options
3. Ensure variety across different collections and meal types
4. Balance nutrition by including different types of recipes
5. Create 7 days with 3 meals per day unless user specifies otherwise
6. Include similarity scores in the output for transparency

Return JSON format:
{
  "meal_plan": [
    {
      "day": 1,
      "meals": [
        {
          "meal_type": "breakfast",
          "recipe_id": 123,
          "recipe_name": "Recipe Name",
          "collection": "breakfast-morning",
          "similarity_score": 0.85
        }
      ]
    }
  ],
  "explanation": "Detailed explanation of meal plan choices, highlighting how AI recommendations were used to match your preferences"
}

CRITICAL: Output ONLY the JSON object. No markdown, no extra text.

================================================================================

⏳ Sending request to Gemini API...

================================================================================
📥 EXACT RESPONSE FROM GEMINI:
================================================================================

{
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
        },
        {
          "meal_type": "dinner",
          "recipe_id": 12367,
          "recipe_name": "Asian Vegetable Stir-fry",
          "collection": "quick-light", 
          "similarity_score": 0.823
        }
      ]
    },
    // ... more days
  ],
  "explanation": "I've created a 7-day healthy vegetarian meal plan focusing on Mediterranean and Asian cuisines as per your preferences. The plan prioritizes high-scoring recipes from our plant-based and quick-light collections, ensuring variety while avoiding nuts due to your allergy. Each day balances nutrition with quick-cooking methods you prefer, featuring protein-rich quinoa, fresh vegetables, and flavorful one-pot dishes. The similarity scores show how well each recipe matches your original request, with most scoring above 0.8 for excellent relevance."
}

================================================================================

🔄 Parsing Gemini response...
✅ Gemini response parsed successfully
```

### Stage 6: Final Quality Analysis
```
📊 STEP 5: Adding Enhanced Metadata
📈 Quality Metrics:
   • Average Recipe Similarity: 0.821
   • Collections Used: ['plant-based', 'quick-light', 'fresh-cold']
   • User Preferences Applied: true

================================================================================
🎉 RAG MEAL PLAN THINKING PROCESS COMPLETE
================================================================================
✅ Final Meal Plan Generated:
   • Recipes Found: 27
   • AI Enhanced: true
   • Processing Quality: 0.821 average similarity
   • Collections: 3 different types
================================================================================
```

## Benefits of This Logging System

### 🔍 Transparency
- **See exactly what data flows** through each stage
- **Verify user preferences** are properly captured and used
- **Track recipe quality** through similarity scores
- **Monitor AI decision-making** at each step

### 🐛 Debugging  
- **Identify where the process fails** if results are poor
- **See if user preferences** are being lost along the way
- **Verify prompt construction** is including all relevant context
- **Check recipe collection diversity** and quality

### 📊 Optimization
- **Measure processing times** at each stage
- **Track recommendation quality** via similarity scores
- **Identify bottlenecks** in the RAG pipeline
- **Monitor user preference effectiveness**

### 🧪 Testing
- **Validate prompt engineering** changes 
- **Compare before/after** optimization results
- **Ensure conversation context** flows properly
- **Verify fallback mechanisms** work correctly

## How to Use These Logs

### Development
1. **Run a meal plan creation** in your local environment
2. **Check the logs** to see the complete thinking process
3. **Verify each stage** is working as expected
4. **Identify improvements** needed in prompts or data flow

### Production Monitoring
1. **Monitor average similarity scores** for quality
2. **Track processing times** for performance
3. **Watch for fallback usage** indicating issues
4. **Analyze user preference effectiveness**

### Debugging Issues
1. **User reports poor recommendations**: Check similarity scores and recipe collections
2. **Slow performance**: Look at processing times per stage  
3. **Preferences not working**: Verify user context extraction and prompt inclusion
4. **AI giving weird results**: Examine exact prompts sent to Gemini

This logging system gives you complete visibility into the AI's "thinking" process, making it easy to understand, debug, and optimize the meal planning recommendations.