# How to View RAG Thinking Process Logs

## 🚀 Quick Access Commands (Works on Any Computer)

### **Method 1: Real-Time Log Monitoring (Recommended)**
```bash
# Navigate to your MealMateAI directory
cd /path/to/your/MealMateAI

# Follow logs in real-time - run this BEFORE sending a prompt
docker-compose logs -f meal-planner-service
```

### **Method 2: View Recent Logs**
```bash
# Check last 100 lines of logs
docker-compose logs --tail=100 meal-planner-service

# Check logs from last 10 minutes
docker-compose logs --since=10m meal-planner-service
```

### **Method 3: Search for Specific Logs**
```bash
# Look for the thinking process start
docker-compose logs meal-planner-service | grep "🧠 STARTING RAG"

# Look for Gemini prompts
docker-compose logs meal-planner-service | grep "📤 EXACT PROMPT"

# Look for user context
docker-compose logs meal-planner-service | grep "🎯 User Preferences"
```

## 🎯 **Step-by-Step: How to See Your Logs**

### **Step 1: Start Log Monitoring**
Open your terminal and run:
```bash
# Navigate to your MealMateAI project directory
cd /path/to/your/MealMateAI

# Start monitoring logs in real-time
docker-compose logs -f meal-planner-service
```

Replace `/path/to/your/MealMateAI` with your actual project path.

### **Step 2: Send a Prompt in the Chat**
Go to your frontend and send any meal planning prompt like:
- "I want healthy vegetarian meals for 7 days"
- "Give me high protein low carb meals"
- "I need quick meals for a busy week"

### **Step 3: Watch the Magic** ✨
You'll see the complete thinking process unfold in real-time:

```
================================================================================
🧠 STARTING RAG MEAL PLAN THINKING PROCESS
================================================================================

📋 STEP 1: Gathering User Context
👤 User ID: 1
💬 Original Prompt: 'I want healthy vegetarian meals for 7 days'
🎯 User Preferences Retrieved:
   • Dietary Restrictions: ['vegetarian']
   • Allergies: []
   • Cuisine Preferences: []
   • Cooking Style: []
   • Spice Tolerance: unknown
   • Portion Preference: unknown

📚 STEP 2: Analyzing Meal Plan History
🗂️ Recent Meal Plans (last 3): []
   ⚪ No previous meal plans found - first time user

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

⚡ Calling Recipe Service /recommendations endpoint...
📥 Recipe Service Response Status: success
🔢 Total Results Returned: 27

✅ SUCCESS: AI recommendations returned 27 recipes

🔍 Recipe Service Query Analysis:
   • Detected Preferences: ['healthy', 'vegetarian']
   • Detected Restrictions: ['vegetarian']
   • Meal Context: meal plan
   • Collections Searched: ['plant-based', 'quick-light', 'fresh-cold']
   • Processing Time: 1850ms

🎯 Generated Queries by Collection:
     plant-based: ["healthy vegetarian meals", "nutritious plant protein"]
     quick-light: ["quick vegetarian meals", "light healthy dishes"]
     fresh-cold: ["fresh vegetable dishes", "healthy salads"]

📋 Sample Retrieved Recipes (top 5):
   1. Mediterranean Quinoa Bowl (Collection: plant-based, Score: 0.892)
   2. Fresh Garden Salad (Collection: fresh-cold, Score: 0.845)
   3. Quick Veggie Stir-fry (Collection: quick-light, Score: 0.823)
   ...

🎭 STEP 4: Gemini Meal Plan Generation
📊 Analyzing recipe collections and user context...
📂 Recipe Collections Organized:
   • plant-based: 12 recipes (avg score: 0.834)
   • quick-light: 8 recipes (avg score: 0.792)
   • fresh-cold: 7 recipes (avg score: 0.756)

✍️ Constructing Enhanced Prompt for Gemini...
================================================================================
📤 EXACT PROMPT SENT TO GEMINI:
================================================================================

Create a personalized meal plan based on this request: I want healthy vegetarian meals for 7 days

USER PROFILE CONTEXT:
- Dietary Restrictions: vegetarian
- Allergies: 
- Cuisine Preferences: 
- Cooking Style: 
- Spice Tolerance: unknown
- Portion Preference: unknown
- Disliked Ingredients: 

AVAILABLE AI-RECOMMENDED RECIPES (organized by collection with similarity scores):
{
  "plant-based": [
    {
      "recipe_id": "12345",
      "recipe_name": "Mediterranean Quinoa Bowl",
      "similarity_score": 0.892,
      ...
    }
  ],
  ...
}

INSTRUCTIONS:
1. Prioritize recipes with higher similarity_score (closer to 1.0)
2. Use recipe collections for smart meal type assignment
...

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
        ...
      ]
    }
  ],
  "explanation": "I've created a 7-day healthy vegetarian meal plan..."
}

================================================================================

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

## 🔧 **Pro Tips**

### **Filter for Specific Information**
```bash
# Just see the prompts sent to Gemini
docker-compose logs meal-planner-service | grep -A 50 "📤 EXACT PROMPT"

# Just see user preferences
docker-compose logs meal-planner-service | grep -A 10 "🎯 User Preferences"

# Just see recipe recommendations
docker-compose logs meal-planner-service | grep -A 20 "📋 Sample Retrieved Recipes"
```

### **Save Logs to File**
```bash
# Save current logs to file
docker-compose logs meal-planner-service > meal_planning_logs.txt

# Save logs with timestamps
docker-compose logs -t meal-planner-service > meal_planning_logs_with_time.txt
```

### **Watch for Issues**
```bash
# Look for errors or warnings
docker-compose logs meal-planner-service | grep -E "(ERROR|WARNING|❌)"

# Look for fallback usage (indicates AI issues)
docker-compose logs meal-planner-service | grep "Falling back"
```

## 🎉 **What You'll See**

With this enhanced logging, you can now **literally see with your eyes**:

✅ **What user preferences** are captured and passed along  
✅ **What queries** the AI generates for recipe search  
✅ **What recipes** are found and their similarity scores  
✅ **The exact prompt** sent to Gemini (with all context)  
✅ **Gemini's exact response** (raw, unfiltered)  
✅ **Quality metrics** showing how well the system performed  

This gives you complete transparency into the AI's "thinking" process!