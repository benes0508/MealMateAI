"""
⚠️⚠️⚠️ WARNING: HIGH COST RISK ⚠️⚠️⚠️

MealMateAI Full Performance Test INCLUDING AI ENDPOINTS
This test file exercises AI-powered features that WILL INCUR COSTS!

DO NOT RUN THIS TEST WITHOUT:
1. Setting strict budget limits
2. Running cost_monitor.py in parallel
3. Having emergency shutdown ready
4. Management approval for AI testing

ESTIMATED COSTS:
- Per user per hour: $5-10
- 10 users for 1 hour: $50-100
- 100 users for 1 hour: $500-1000 💸💸💸

⚠️⚠️⚠️ YOU HAVE BEEN WARNED ⚠️⚠️⚠️
"""

from locust import HttpUser, task, between, events
import random
import json
import uuid
import time
import os
import sys
from datetime import datetime
from faker import Faker

# SAFETY CHECKS
if os.getenv("PERFORMANCE_TEST_MODE") != "true":
    print("❌ ERROR: PERFORMANCE_TEST_MODE not set to 'true'")
    print("Set: export PERFORMANCE_TEST_MODE=true")
    sys.exit(1)

if not os.getenv("GEMINI_API_DAILY_LIMIT"):
    print("❌ ERROR: GEMINI_API_DAILY_LIMIT not set")
    print("Set: export GEMINI_API_DAILY_LIMIT=50")
    sys.exit(1)

if os.getenv("CONFIRM_AI_TESTING") != "yes":
    print("❌ ERROR: AI testing not confirmed")
    print("Set: export CONFIRM_AI_TESTING=yes")
    print("⚠️  This will incur API costs!")
    sys.exit(1)

# Cost tracking
total_ai_calls = 0
estimated_cost = 0.0
start_time = time.time()

fake = Faker()

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Show warnings when test starts"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    ⚠️  DANGER ZONE ⚠️                        ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  YOU ARE ABOUT TO RUN AI-POWERED TESTS                      ║
    ║  THIS WILL INCUR REAL COSTS ON YOUR GEMINI API             ║
    ║                                                              ║
    ║  Estimated costs:                                           ║
    ║  - Per meal plan: $0.01-0.05                               ║
    ║  - Per recommendation: $0.001-0.01                         ║
    ║  - Per grocery list: $0.005-0.02                           ║
    ║                                                              ║
    ║  Press Ctrl+C NOW if you want to cancel!                    ║
    ║  Starting in 10 seconds...                                  ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    time.sleep(10)
    print("🚀 Starting AI tests... Monitor costs closely!")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Show cost summary when test stops"""
    runtime = time.time() - start_time
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    Cost Summary                              ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Total AI API Calls: {total_ai_calls:>8}                           ║
    ║  Estimated Cost: ${estimated_cost:>11.2f}                          ║
    ║  Runtime: {runtime/60:>15.1f} minutes                       ║
    ║  Cost per minute: ${estimated_cost/(runtime/60):>10.2f}                     ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

class MealMateAIFullUser(HttpUser):
    """
    Full test including AI-powered features.
    ⚠️ WILL INCUR COSTS! Use with extreme caution!
    """
    
    wait_time = between(5, 10)  # Longer wait to reduce API calls
    
    def on_start(self):
        """Initialize user with authentication"""
        self.user_id = None
        self.auth_token = None
        self.email = f"ai_test_{uuid.uuid4().hex[:8]}@test.local"
        self.password = "TestPass123!"
        self.meal_plan_id = None
        self.conversation_history = []
        
        # Register and login
        self.register_and_login()
        
        # Set up preferences for better AI results
        self.setup_user_preferences()
    
    def register_and_login(self):
        """Register and authenticate user"""
        # Register
        with self.client.post("/api/auth/register",
                             json={
                                 "email": self.email,
                                 "password": self.password,
                                 "name": fake.name()
                             },
                             catch_response=True) as response:
            if response.status_code not in [200, 201]:
                print(f"❌ Registration failed: {response.status_code}")
                response.failure("Registration failed")
                return
        
        # Login
        with self.client.post("/api/auth/login",
                             json={
                                 "email": self.email,
                                 "password": self.password
                             },
                             catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token", data.get("token"))
                self.user_id = data.get("user", {}).get("id", data.get("user_id"))
                
                self.client.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                print(f"✅ Authenticated: {self.email}")
            else:
                print(f"❌ Login failed: {response.status_code}")
                response.failure("Login failed")
    
    def setup_user_preferences(self):
        """Set user preferences for AI testing"""
        if not self.user_id or not self.auth_token:
            return
        
        preferences = {
            "dietary_restrictions": random.choice([[], ["vegetarian"], ["vegan"]]),
            "allergies": random.choice([[], ["nuts"], ["dairy"]]),
            "cuisine_preferences": random.choice([["italian"], ["asian"], ["mexican"]]),
            "cooking_skill": "intermediate",
            "meal_prep_time": 30,
            "servings": 2,
            "budget": "medium"
        }
        
        self.client.put(f"/api/users/{self.user_id}/preferences",
                       json=preferences,
                       name="Setup Preferences")
    
    @task(1)
    def ai_recipe_recommendations(self):
        """
        Get AI-powered recipe recommendations
        ⚠️ COSTS: ~$0.001-0.01 per call
        """
        global total_ai_calls, estimated_cost
        
        if not self.auth_token:
            return
        
        # Build conversation for context
        conversation = [
            {"role": "user", "content": random.choice([
                "I want something healthy for dinner",
                "Looking for a quick breakfast",
                "Need a vegetarian lunch option",
                "Craving something sweet for dessert"
            ])},
            {"role": "assistant", "content": "I'll help you find the perfect recipe!"},
            {"role": "user", "content": random.choice([
                "Something that takes less than 30 minutes",
                "I have chicken and vegetables",
                "Preferably something Italian",
                "Low carb would be great"
            ])}
        ]
        
        with self.client.post("/api/recipes/recommendations",
                             json={
                                 "conversation_history": conversation,
                                 "max_results": 5
                             },
                             name="AI Recipe Recommendations",
                             catch_response=True,
                             timeout=30) as response:
            if response.status_code == 200:
                total_ai_calls += 1
                estimated_cost += 0.005  # Estimate
                response.success()
            elif response.status_code == 429:
                print("⚠️ Rate limited - good!")
                response.success()
            else:
                response.failure(f"Recommendations failed: {response.status_code}")
    
    @task(1)
    def ai_meal_plan_generation(self):
        """
        Generate complete meal plan using RAG
        ⚠️ COSTS: ~$0.01-0.05 per call
        """
        global total_ai_calls, estimated_cost
        
        if not self.auth_token:
            return
        
        # Check cost limit
        if estimated_cost > float(os.getenv("GEMINI_API_DAILY_LIMIT", 50)) * 0.8:
            print("⚠️ Approaching budget limit - skipping AI call")
            return
        
        prompts = [
            "I need a 7 day meal plan for weight loss",
            "Create a 5 day vegetarian meal plan",
            "Plan my meals for the week, I love Italian food",
            "I want high protein meals for muscle building",
            "Family meal plan for 4 people, kid-friendly"
        ]
        
        with self.client.post("/api/meal-plans/rag/generate",
                             json={
                                 "user_id": self.user_id,
                                 "prompt": random.choice(prompts),
                                 "days": random.choice([3, 5, 7]),
                                 "meals_per_day": 3
                             },
                             name="AI Meal Plan Generation",
                             catch_response=True,
                             timeout=60) as response:
            if response.status_code == 200:
                total_ai_calls += 1
                estimated_cost += 0.03  # Estimate
                data = response.json()
                self.meal_plan_id = data.get("id")
                print(f"💰 Generated meal plan #{self.meal_plan_id} (cost: ~$0.03)")
                response.success()
            elif response.status_code == 429:
                print("⚠️ Rate limited - good!")
                response.success()
            else:
                response.failure(f"Meal plan generation failed: {response.status_code}")
    
    @task(2)
    def text_input_meal_planning(self):
        """
        Natural language meal planning
        ⚠️ COSTS: ~$0.02-0.04 per call
        """
        global total_ai_calls, estimated_cost
        
        if not self.auth_token:
            return
        
        # Check cost limit
        if estimated_cost > float(os.getenv("GEMINI_API_DAILY_LIMIT", 50)) * 0.8:
            print("⚠️ Approaching budget limit - skipping AI call")
            return
        
        requests = [
            "Plan healthy meals for next week, I'm trying to eat more vegetables",
            "I have chicken, rice, and broccoli. What can I make this week?",
            "Create a romantic dinner menu for this weekend",
            "Quick and easy breakfast ideas for busy mornings",
            "Low budget meals for a college student"
        ]
        
        with self.client.post("/api/meal-plans/text-input",
                             json={
                                 "user_id": self.user_id,
                                 "input_text": random.choice(requests)
                             },
                             name="Text Input Meal Planning",
                             catch_response=True,
                             timeout=45) as response:
            if response.status_code == 200:
                total_ai_calls += 1
                estimated_cost += 0.025  # Estimate
                data = response.json()
                self.meal_plan_id = data.get("id")
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Text planning failed: {response.status_code}")
    
    @task(1)
    def ai_grocery_list_generation(self):
        """
        Generate grocery list from meal plan
        ⚠️ COSTS: ~$0.005-0.02 per call
        """
        global total_ai_calls, estimated_cost
        
        if not self.meal_plan_id or not self.auth_token:
            # Try to get existing meal plan first
            self.get_existing_meal_plan()
            if not self.meal_plan_id:
                return
        
        # Force regeneration occasionally
        force_regenerate = random.random() < 0.2  # 20% chance
        
        url = f"/api/meal-plans/{self.meal_plan_id}/grocery-list"
        if force_regenerate:
            url += "?forceRegenerate=true"
        
        with self.client.get(url,
                           name="AI Grocery List Generation",
                           catch_response=True,
                           timeout=30) as response:
            if response.status_code == 200:
                if force_regenerate:
                    total_ai_calls += 1
                    estimated_cost += 0.01  # Estimate
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Grocery list failed: {response.status_code}")
    
    @task(3)
    def collection_specific_search(self):
        """
        Search within specific recipe collections (uses AI for query generation)
        ⚠️ COSTS: ~$0.001-0.005 per call
        """
        global total_ai_calls, estimated_cost
        
        if not self.auth_token:
            return
        
        collections = ["protein-mains", "desserts-sweets", "quick-light", "breakfast-morning"]
        collection = random.choice(collections)
        
        queries = {
            "protein-mains": ["grilled chicken", "beef stir fry", "salmon dinner"],
            "desserts-sweets": ["chocolate cake", "fruit tart", "ice cream"],
            "quick-light": ["15 minute meals", "salad", "sandwich"],
            "breakfast-morning": ["pancakes", "eggs benedict", "smoothie bowl"]
        }
        
        query = random.choice(queries[collection])
        
        with self.client.post(f"/api/recipes/collections/{collection}/search",
                             json={
                                 "query": query,
                                 "max_results": 5
                             },
                             name="Collection Search (AI)",
                             catch_response=True,
                             timeout=20) as response:
            if response.status_code == 200:
                total_ai_calls += 1
                estimated_cost += 0.002  # Estimate
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Collection search failed: {response.status_code}")
    
    @task(2)
    def modify_meal_plan_with_ai(self):
        """
        Modify existing meal plan using AI
        ⚠️ COSTS: ~$0.01-0.03 per call
        """
        global total_ai_calls, estimated_cost
        
        if not self.meal_plan_id or not self.auth_token:
            return
        
        # Check cost limit
        if estimated_cost > float(os.getenv("GEMINI_API_DAILY_LIMIT", 50)) * 0.9:
            print("⚠️ 90% of budget used - stopping AI calls")
            return
        
        modifications = [
            "Make the meals more vegetarian friendly",
            "Replace desserts with healthier options",
            "Add more protein to breakfast",
            "Make dinners quicker to prepare",
            "Reduce the amount of dairy"
        ]
        
        with self.client.post(f"/api/meal-plans/{self.meal_plan_id}/edit-with-text",
                             json={
                                 "user_prompt": random.choice(modifications)
                             },
                             name="AI Meal Plan Modification",
                             catch_response=True,
                             timeout=40) as response:
            if response.status_code == 200:
                total_ai_calls += 1
                estimated_cost += 0.02  # Estimate
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Modification failed: {response.status_code}")
    
    @task(5)
    def mixed_safe_operations(self):
        """Balance with safe operations to reduce AI call frequency"""
        operations = [
            ("/api/recipes", "GET", None),
            ("/api/recipes/collections", "GET", None),
            (f"/api/users/{self.user_id}/preferences", "GET", None),
            ("/health", "GET", None)
        ]
        
        endpoint, method, data = random.choice(operations)
        
        if method == "GET":
            self.client.get(endpoint, name=f"Safe: {endpoint}")
        else:
            self.client.post(endpoint, json=data, name=f"Safe: {endpoint}")
    
    def get_existing_meal_plan(self):
        """Helper to get existing meal plan ID"""
        if not self.user_id:
            return
        
        with self.client.get(f"/api/meal-plans/user/{self.user_id}",
                            name="Get User Meal Plans",
                            catch_response=True) as response:
            if response.status_code == 200:
                plans = response.json()
                if isinstance(plans, list) and len(plans) > 0:
                    self.meal_plan_id = plans[0].get("id")
                    response.success()
    
    def on_stop(self):
        """Log costs when user stops"""
        print(f"💰 User {self.email} - Estimated cost: ${estimated_cost:.2f}")


class EmergencyStopUser(HttpUser):
    """Emergency stop mechanism if costs spike"""
    
    wait_time = between(10, 20)
    weight = 1  # Low weight
    
    @task
    def monitor_costs(self):
        """Check if we should emergency stop"""
        global estimated_cost
        
        limit = float(os.getenv("GEMINI_API_DAILY_LIMIT", 50))
        
        if estimated_cost > limit * 0.8:
            print(f"""
            🚨🚨🚨 EMERGENCY STOP TRIGGERED 🚨🚨🚨
            Cost exceeded 80% of daily limit!
            Current cost: ${estimated_cost:.2f}
            Limit: ${limit:.2f}
            
            STOPPING ALL TESTS NOW!
            """)
            self.environment.runner.quit()


if __name__ == "__main__":
    confirm = input("""
    ⚠️⚠️⚠️ FINAL WARNING ⚠️⚠️⚠️
    
    This test WILL incur real API costs!
    Estimated: $0.10-1.00 per user per hour
    
    Type 'YES I UNDERSTAND THE COSTS' to continue: """)
    
    if confirm != "YES I UNDERSTAND THE COSTS":
        print("❌ Test cancelled. Good choice!")
        sys.exit(0)
    
    print("""
    Starting full AI test in 5 seconds...
    Press Ctrl+C to abort!
    
    Monitor costs with: python scripts/cost_monitor.py --watch
    """)
    time.sleep(5)