"""
MealMateAI Minimal Performance Test (SAFE - No AI Calls)
This test file only exercises endpoints that don't incur API costs.
Safe to run for extended periods without budget concerns.
"""

from locust import HttpUser, task, between
import random
import json
import uuid
from datetime import datetime

class MealMateMinimalUser(HttpUser):
    """
    Simulates basic user interactions without AI features.
    Focus on CRUD operations and cached data retrieval.
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user session with registration and login"""
        self.user_id = None
        self.auth_token = None
        self.email = f"perf_test_{uuid.uuid4().hex[:8]}@test.local"
        self.password = "TestPass123!"
        
        # Register user
        with self.client.post("/api/users/register", 
                             json={
                                 "email": self.email,
                                 "password": self.password,
                                 "name": f"Test User {uuid.uuid4().hex[:4]}"
                             },
                             catch_response=True) as response:
            if response.status_code == 200 or response.status_code == 201:
                print(f"✅ Registered user: {self.email}")
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                response.failure(f"Registration failed: {response.status_code}")
        
        # Login
        with self.client.post("/api/users/login",
                             json={
                                 "email": self.email,
                                 "password": self.password
                             },
                             catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token", data.get("token"))
                self.user_id = data.get("user", {}).get("id", data.get("user_id"))
                print(f"✅ Logged in: {self.email}")
                
                # Set authorization header for future requests
                self.client.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
            else:
                print(f"❌ Login failed: {response.status_code}")
                response.failure(f"Login failed: {response.status_code}")
    
    @task(10)
    def browse_recipes(self):
        """Browse recipe collections - most common operation"""
        with self.client.get("/api/recipes",
                            name="Browse Recipes",
                            catch_response=True) as response:
            if response.status_code == 200:
                recipes = response.json()
                if isinstance(recipes, list) and len(recipes) > 0:
                    # Store a recipe ID for later use
                    self.selected_recipe_id = recipes[0].get("id", 1)
            else:
                response.failure(f"Failed to browse recipes: {response.status_code}")
    
    @task(8)
    def search_recipes_basic(self):
        """Basic recipe search without AI"""
        search_terms = ["chicken", "pasta", "salad", "soup", "dessert", "breakfast"]
        query = random.choice(search_terms)
        
        with self.client.get(f"/api/recipes/search?query={query}",
                            name="Search Recipes (Basic)",
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Search failed: {response.status_code}")
    
    @task(5)
    def view_recipe_details(self):
        """View individual recipe details"""
        if hasattr(self, 'selected_recipe_id'):
            recipe_id = self.selected_recipe_id
        else:
            recipe_id = random.randint(1, 100)  # Fallback to random ID
        
        with self.client.get(f"/api/recipes/{recipe_id}",
                            name="View Recipe Details",
                            catch_response=True) as response:
            if response.status_code == 404:
                # Recipe not found is acceptable
                response.success()
            elif response.status_code != 200:
                response.failure(f"Failed to get recipe: {response.status_code}")
    
    @task(3)
    def get_recipe_collections(self):
        """Get available recipe collections"""
        with self.client.get("/api/recipes/collections",
                            name="Get Collections",
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get collections: {response.status_code}")
    
    @task(2)
    def get_collection_info(self):
        """Get information about a specific collection"""
        collections = ["protein-mains", "desserts-sweets", "quick-light", 
                      "breakfast-morning", "fresh-cold", "baked-breads"]
        collection = random.choice(collections)
        
        with self.client.get(f"/api/recipes/collections/{collection}/info",
                            name="Get Collection Info",
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get collection info: {response.status_code}")
    
    @task(4)
    def get_user_preferences(self):
        """Get current user preferences"""
        if not self.user_id or not self.auth_token:
            return
        
        with self.client.get(f"/api/users/{self.user_id}/preferences",
                            name="Get User Preferences",
                            catch_response=True) as response:
            if response.status_code == 404:
                # No preferences yet is acceptable
                response.success()
            elif response.status_code != 200:
                response.failure(f"Failed to get preferences: {response.status_code}")
    
    @task(2)
    def update_user_preferences(self):
        """Update user preferences"""
        if not self.user_id or not self.auth_token:
            return
        
        preferences = {
            "dietary_restrictions": random.choice([[], ["vegetarian"], ["vegan"], ["gluten-free"]]),
            "allergies": random.choice([[], ["nuts"], ["dairy"], ["shellfish"]]),
            "cuisine_preferences": random.choice([["italian"], ["asian"], ["mexican"], ["american"]]),
            "cooking_skill": random.choice(["beginner", "intermediate", "advanced"]),
            "kitchen_equipment": ["oven", "stove", "microwave"],
            "meal_prep_time": random.choice([15, 30, 45, 60])
        }
        
        with self.client.put(f"/api/users/{self.user_id}/preferences",
                            json=preferences,
                            name="Update Preferences",
                            catch_response=True) as response:
            if response.status_code not in [200, 201]:
                response.failure(f"Failed to update preferences: {response.status_code}")
    
    @task(3)
    def get_user_meal_plans(self):
        """Get user's existing meal plans (if any)"""
        if not self.user_id or not self.auth_token:
            return
        
        with self.client.get(f"/api/meal-plans/user/{self.user_id}",
                            name="Get User Meal Plans",
                            catch_response=True) as response:
            if response.status_code == 404 or response.status_code == 200:
                # No meal plans or successful retrieval
                response.success()
                if response.status_code == 200:
                    plans = response.json()
                    if isinstance(plans, list) and len(plans) > 0:
                        self.existing_meal_plan_id = plans[0].get("id")
            else:
                response.failure(f"Failed to get meal plans: {response.status_code}")
    
    @task(2)
    def get_cached_grocery_list(self):
        """Get grocery list (only if cached, no generation)"""
        if not hasattr(self, 'existing_meal_plan_id'):
            return  # Skip if no meal plan exists
        
        # Only get cached version, don't force regeneration
        with self.client.get(f"/api/meal-plans/{self.existing_meal_plan_id}/grocery-list",
                            name="Get Cached Grocery List",
                            catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()  # Both are acceptable
            else:
                response.failure(f"Failed to get grocery list: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Periodic health check"""
        with self.client.get("/health",
                            name="Health Check",
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(1)
    def get_recipe_categories(self):
        """Get recipe categories"""
        with self.client.get("/api/recipes/categories",
                            name="Get Categories",
                            catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get categories: {response.status_code}")
    
    def on_stop(self):
        """Cleanup when user stops"""
        if self.auth_token:
            print(f"👋 User session ended: {self.email}")
            # Could implement logout here if needed


class MealMateMinimalLoadTest(HttpUser):
    """
    Alternative minimal user for mixed load testing.
    Focuses more on read operations.
    """
    
    tasks = [MealMateMinimalUser]
    wait_time = between(2, 5)
    
    def on_start(self):
        """Simple initialization"""
        print(f"🚀 Starting minimal load test")
    
    def on_stop(self):
        """Simple cleanup"""
        print(f"🏁 Ending minimal load test")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║           MealMateAI Minimal Performance Test                ║
    ║                                                              ║
    ║  ✅ SAFE: No AI API calls                                   ║
    ║  ✅ SAFE: No cost implications                              ║
    ║  ✅ SAFE: Only tests CRUD and cached operations             ║
    ║                                                              ║
    ║  Endpoints tested:                                          ║
    ║  - User registration and authentication                     ║
    ║  - Recipe browsing and search (basic)                       ║
    ║  - User preferences CRUD                                    ║
    ║  - Cached meal plans and grocery lists                      ║
    ║  - Recipe collections and categories                        ║
    ║                                                              ║
    ║  Run with: locust -f locustfile_minimal.py                  ║
    ╚══════════════════════════════════════════════════════════════╝
    """)