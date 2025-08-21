"""
MealMateAI Comprehensive Performance Test
Tests all key components including AI endpoints with rate limit bypass.
Focuses on measuring actual performance metrics for the report.
"""

from locust import HttpUser, task, between, events
import random
import json
import uuid
import time
from datetime import datetime
import statistics

# Performance metrics collection
performance_metrics = {
    "ai_generation_times": [],
    "vector_search_times": [],
    "database_query_times": [],
    "auth_times": [],
    "error_counts": {
        "ai_errors": 0,
        "db_errors": 0,
        "auth_errors": 0,
        "search_errors": 0
    }
}

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate performance report when test stops"""
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    Performance Report                        ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  AI Generation Performance:                                  ║
    ║  ├─ Average: {statistics.mean(performance_metrics["ai_generation_times"]) if performance_metrics["ai_generation_times"] else 0:.2f}ms                                      ║
    ║  ├─ P95: {statistics.quantiles(performance_metrics["ai_generation_times"], n=20)[18] if len(performance_metrics["ai_generation_times"]) >= 20 else 0:.2f}ms                                          ║
    ║  └─ Errors: {performance_metrics["error_counts"]["ai_errors"]}                                           ║
    ║                                                              ║
    ║  Vector Search Performance:                                  ║
    ║  ├─ Average: {statistics.mean(performance_metrics["vector_search_times"]) if performance_metrics["vector_search_times"] else 0:.2f}ms                                      ║
    ║  ├─ P95: {statistics.quantiles(performance_metrics["vector_search_times"], n=20)[18] if len(performance_metrics["vector_search_times"]) >= 20 else 0:.2f}ms                                          ║
    ║  └─ Errors: {performance_metrics["error_counts"]["search_errors"]}                                           ║
    ║                                                              ║
    ║  Database Performance:                                       ║
    ║  ├─ Average: {statistics.mean(performance_metrics["database_query_times"]) if performance_metrics["database_query_times"] else 0:.2f}ms                                      ║
    ║  └─ Errors: {performance_metrics["error_counts"]["db_errors"]}                                           ║
    ║                                                              ║
    ║  Authentication Performance:                                 ║
    ║  ├─ Average: {statistics.mean(performance_metrics["auth_times"]) if performance_metrics["auth_times"] else 0:.2f}ms                                      ║
    ║  └─ Errors: {performance_metrics["error_counts"]["auth_errors"]}                                           ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

class PerformanceTestUser(HttpUser):
    """Comprehensive performance testing user with bypass headers"""
    
    wait_time = between(2, 4)
    
    def on_start(self):
        """Initialize user with bypass headers and authentication"""
        # Add bypass header for rate limiting
        self.client.headers.update({
            "x-bypass-rate-limit": "true",
            "Content-Type": "application/json"
        })
        
        self.user_id = None
        self.auth_token = None
        self.email = f"perf_test_{uuid.uuid4().hex[:8]}@test.local"
        self.password = "TestPass123!"
        self.meal_plan_id = None
        
        # Authenticate user
        self.authenticate_user()
    
    def authenticate_user(self):
        """Register and login user with performance tracking"""
        start_time = time.time()
        
        # Register
        with self.client.post("/api/users/register",
                             json={
                                 "email": self.email,
                                 "password": self.password,
                                 "name": f"Perf Test User {uuid.uuid4().hex[:4]}"
                             },
                             catch_response=True) as response:
            if response.status_code in [200, 201, 409]:  # 409 = already exists
                # Login
                with self.client.post("/api/users/login",
                                     json={
                                         "email": self.email,
                                         "password": self.password
                                     },
                                     catch_response=True) as login_response:
                    if login_response.status_code == 200:
                        data = login_response.json()
                        self.auth_token = data.get("access_token", data.get("token"))
                        self.user_id = data.get("user", {}).get("id", data.get("user_id"))
                        
                        # Update headers with auth token
                        self.client.headers.update({
                            "Authorization": f"Bearer {self.auth_token}"
                        })
                        
                        auth_time = (time.time() - start_time) * 1000
                        performance_metrics["auth_times"].append(auth_time)
                        print(f"✅ Auth completed in {auth_time:.2f}ms")
                    else:
                        performance_metrics["error_counts"]["auth_errors"] += 1
                        login_response.failure("Login failed")
            else:
                performance_metrics["error_counts"]["auth_errors"] += 1
                response.failure("Registration failed")
    
    @task(15)
    def test_database_performance(self):
        """Test basic database query performance"""
        start_time = time.time()
        
        with self.client.get("/api/recipes",
                            name="Database Query (Recipes)",
                            catch_response=True) as response:
            query_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                performance_metrics["database_query_times"].append(query_time)
                response.success()
            else:
                performance_metrics["error_counts"]["db_errors"] += 1
                response.failure(f"DB query failed: {response.status_code}")
    
    @task(10)
    def test_vector_search_performance(self):
        """Test Qdrant vector search performance"""
        search_queries = [
            "healthy chicken dinner",
            "quick breakfast ideas", 
            "vegetarian pasta recipes",
            "chocolate dessert recipes",
            "low carb meals"
        ]
        
        query = random.choice(search_queries)
        start_time = time.time()
        
        with self.client.post("/api/recipes/search",
                             json={
                                 "query": query,
                                 "max_results": 5
                             },
                             name="Vector Search",
                             catch_response=True) as response:
            search_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                performance_metrics["vector_search_times"].append(search_time)
                response.success()
                print(f"🔍 Vector search: {search_time:.2f}ms")
            else:
                performance_metrics["error_counts"]["search_errors"] += 1
                response.failure(f"Vector search failed: {response.status_code}")
    
    @task(5)
    def test_collection_search_performance(self):
        """Test collection-specific search performance"""
        collections = ["protein-mains", "desserts-sweets", "quick-light", "breakfast-morning"]
        collection = random.choice(collections)
        
        queries = {
            "protein-mains": ["grilled salmon", "chicken stir fry", "beef tacos"],
            "desserts-sweets": ["chocolate cake", "fruit pie", "ice cream"],
            "quick-light": ["15 minute meals", "light salad", "quick sandwich"],
            "breakfast-morning": ["pancakes", "eggs", "smoothie"]
        }
        
        query = random.choice(queries[collection])
        start_time = time.time()
        
        with self.client.post(f"/api/recipes/collections/{collection}/search",
                             json={
                                 "query": query,
                                 "max_results": 3
                             },
                             name="Collection Search",
                             catch_response=True) as response:
            search_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                performance_metrics["vector_search_times"].append(search_time)
                response.success()
            else:
                performance_metrics["error_counts"]["search_errors"] += 1
                response.failure(f"Collection search failed: {response.status_code}")
    
    @task(3)
    def test_ai_recommendations_performance(self):
        """Test AI recommendation generation performance (COSTS MONEY!)"""
        if not self.auth_token:
            return
        
        conversation = [
            {"role": "user", "content": "I want something healthy for lunch"},
            {"role": "assistant", "content": "I can help with healthy lunch ideas!"},
            {"role": "user", "content": "Something with vegetables would be great"}
        ]
        
        start_time = time.time()
        
        with self.client.post("/api/recipes/recommendations",
                             json={
                                 "conversation_history": conversation,
                                 "max_results": 3
                             },
                             name="AI Recommendations",
                             catch_response=True,
                             timeout=30) as response:
            ai_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                performance_metrics["ai_generation_times"].append(ai_time)
                response.success()
                print(f"🤖 AI recommendation: {ai_time:.2f}ms")
            elif response.status_code == 429:
                # Rate limited - expected
                response.success()
            else:
                performance_metrics["error_counts"]["ai_errors"] += 1
                response.failure(f"AI recommendation failed: {response.status_code}")
    
    @task(2)
    def test_meal_plan_generation_performance(self):
        """Test full meal plan generation (LIMITED - COSTS MONEY!)"""
        if not self.auth_token or not self.user_id:
            return
        
        # Only occasionally test this to limit costs
        if random.random() > 0.3:  # 30% chance
            return
        
        start_time = time.time()
        
        with self.client.post("/api/meal-plans/text-input",
                             json={
                                 "user_id": self.user_id,
                                 "input_text": "Create a 3 day healthy meal plan with easy recipes"
                             },
                             name="AI Meal Plan Generation",
                             catch_response=True,
                             timeout=60) as response:
            generation_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                performance_metrics["ai_generation_times"].append(generation_time)
                data = response.json()
                self.meal_plan_id = data.get("id")
                response.success()
                print(f"🍽️ Meal plan generated: {generation_time:.2f}ms")
            elif response.status_code == 429:
                response.success()
            else:
                performance_metrics["error_counts"]["ai_errors"] += 1
                response.failure(f"Meal plan generation failed: {response.status_code}")
    
    @task(8)
    def test_cached_operations(self):
        """Test cached operations performance"""
        operations = [
            ("/api/recipes/collections", "GET", "Collections List"),
            ("/api/recipes/categories", "GET", "Categories List"),
            ("/health", "GET", "Health Check")
        ]
        
        endpoint, method, name = random.choice(operations)
        start_time = time.time()
        
        with self.client.get(endpoint, name=name, catch_response=True) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                performance_metrics["database_query_times"].append(response_time)
                response.success()
            else:
                performance_metrics["error_counts"]["db_errors"] += 1
                response.failure(f"{name} failed: {response.status_code}")
    
    @task(4)
    def test_user_preferences_performance(self):
        """Test user preferences CRUD performance"""
        if not self.user_id or not self.auth_token:
            return
        
        start_time = time.time()
        
        # Test GET preferences
        with self.client.get(f"/api/users/{self.user_id}/preferences",
                            name="Get User Preferences",
                            catch_response=True) as response:
            get_time = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 404]:  # 404 = no preferences yet
                performance_metrics["database_query_times"].append(get_time)
                response.success()
            else:
                performance_metrics["error_counts"]["db_errors"] += 1
                response.failure(f"Get preferences failed: {response.status_code}")
        
        # Test PUT preferences
        preferences = {
            "dietary_restrictions": random.choice([[], ["vegetarian"], ["vegan"]]),
            "allergies": random.choice([[], ["nuts"], ["dairy"]]),
            "cuisine_preferences": ["italian", "asian"],
            "cooking_skill": "intermediate"
        }
        
        start_time = time.time()
        
        with self.client.put(f"/api/users/{self.user_id}/preferences",
                            json=preferences,
                            name="Update User Preferences",
                            catch_response=True) as response:
            put_time = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 201]:
                performance_metrics["database_query_times"].append(put_time)
                response.success()
            else:
                performance_metrics["error_counts"]["db_errors"] += 1
                response.failure(f"Update preferences failed: {response.status_code}")
    
    @task(1)
    def test_grocery_list_performance(self):
        """Test grocery list generation (if meal plan exists)"""
        if not self.meal_plan_id:
            # Try to get existing meal plans
            with self.client.get(f"/api/meal-plans/user/{self.user_id}",
                                name="Get User Meal Plans",
                                catch_response=True) as response:
                if response.status_code == 200:
                    plans = response.json()
                    if isinstance(plans, list) and len(plans) > 0:
                        self.meal_plan_id = plans[0].get("id")
        
        if not self.meal_plan_id:
            return
        
        start_time = time.time()
        
        with self.client.get(f"/api/meal-plans/{self.meal_plan_id}/grocery-list",
                            name="Get Grocery List",
                            catch_response=True,
                            timeout=30) as response:
            grocery_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check if it was generated or cached
                if grocery_time > 1000:  # If > 1 second, likely generated
                    performance_metrics["ai_generation_times"].append(grocery_time)
                    print(f"🛒 Grocery list generated: {grocery_time:.2f}ms")
                else:
                    performance_metrics["database_query_times"].append(grocery_time)
                    print(f"🛒 Grocery list cached: {grocery_time:.2f}ms")
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                performance_metrics["error_counts"]["ai_errors"] += 1
                response.failure(f"Grocery list failed: {response.status_code}")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         MealMateAI Comprehensive Performance Test            ║
    ║                                                              ║
    ║  ⚡ Tests all key performance metrics:                       ║
    ║  ├─ Database query performance                              ║
    ║  ├─ Vector search (Qdrant) performance                     ║
    ║  ├─ AI generation performance                               ║
    ║  ├─ Authentication performance                              ║
    ║  └─ Caching effectiveness                                   ║
    ║                                                              ║
    ║  ⚠️  AI tests are limited to control costs                 ║
    ║  ✅ Rate limiting bypassed for accurate testing             ║
    ╚══════════════════════════════════════════════════════════════╝
    """)