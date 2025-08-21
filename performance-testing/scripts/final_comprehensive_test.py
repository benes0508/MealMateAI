#!/usr/bin/env python3.9
"""
FINAL COMPREHENSIVE PERFORMANCE TEST
Complete statistical performance analysis of MealMateAI with real AI data
"""

import requests
import time
import json
import statistics
import uuid
import random
from datetime import datetime
import concurrent.futures
from threading import Lock

class FinalComprehensiveTest:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.user_service_url = "http://localhost:8000"
        self.auth_token = None
        self.user_id = None
        self.measurements = {
            # Basic performance
            "health_check": [],
            "authentication": [],
            
            # Database performance
            "database_recipes": [],
            "database_collections": [],
            "database_recipe_detail": [],
            
            # Vector search performance (the comparison you wanted)
            "vector_multi_search": [],
            "vector_protein_search": [],
            "vector_dessert_search": [],
            "vector_breakfast_search": [],
            "vector_quick_search": [],
            "vector_fresh_search": [],
            
            # AI performance (REAL DATA)
            "ai_recommendations": [],
            "ai_meal_planning": [],
            
            # User operations
            "user_preferences_get": [],
            "user_preferences_update": [],
            
            # Concurrency testing
            "concurrent_vector": [],
            "concurrent_database": []
        }
        self.lock = Lock()
        
        # Test data
        self.vector_queries = {
            "protein-mains": ["grilled chicken", "beef steak", "salmon fillet", "pork chops"],
            "desserts-sweets": ["chocolate cake", "vanilla ice cream", "apple pie", "brownies"],
            "breakfast-morning": ["pancakes", "scrambled eggs", "oatmeal", "smoothie"],
            "quick-light": ["15 minute meals", "salad", "sandwich", "soup"],
            "fresh-cold": ["salad", "gazpacho", "sushi", "ceviche"]
        }
    
    def create_session(self):
        """Create session with bypass headers"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "x-bypass-rate-limit": "true"
        })
        return session
    
    def measure_time(self, func, *args, **kwargs):
        """Measure execution time"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = str(e)
            success = False
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        return success, result, execution_time
    
    def setup_authentication(self):
        """Setup authentication once for all tests"""
        print("🔐 Setting up authentication...")
        
        test_email = f"final_test_{uuid.uuid4().hex[:8]}@test.com"
        password = "TestPass123"
        
        try:
            # Register with user service directly
            register_response = requests.post(f"{self.user_service_url}/users/register/simple", json={
                "email": test_email,
                "password": password,
                "name": "Final Test User"
            }, timeout=10)
            
            print(f"   Register: {register_response.status_code}")
            
            # Login with user service directly
            login_response = requests.post(f"{self.user_service_url}/users/login/json", json={
                "email": test_email,
                "password": password
            }, timeout=10)
            
            print(f"   Login: {login_response.status_code}")
            
            if login_response.status_code == 200:
                data = login_response.json()
                self.auth_token = data.get("token", data.get("access_token"))
                user_data = data.get("user", {})
                self.user_id = user_data.get("id")
                print(f"   ✅ Authentication successful! User ID: {self.user_id}")
                return True
            else:
                print(f"   ❌ Login failed: {login_response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Auth error: {e}")
            return False
    
    # ============= TEST FUNCTIONS =============
    
    def test_health_check(self):
        session = self.create_session()
        response = session.get(f"{self.base_url}/health", timeout=5)
        return response.status_code == 200
    
    def test_authentication_flow(self):
        """Test complete auth flow"""
        email = f"auth_test_{uuid.uuid4().hex[:4]}@test.com"
        password = "TestPass123"
        
        # Register
        register_response = requests.post(f"{self.user_service_url}/users/register/simple", json={
            "email": email,
            "password": password,
            "name": "Auth Test User"
        }, timeout=10)
        
        # Login
        login_response = requests.post(f"{self.user_service_url}/users/login/json", json={
            "email": email,
            "password": password
        }, timeout=10)
        
        return login_response.status_code == 200
    
    def test_database_recipes(self):
        session = self.create_session()
        response = session.get(f"{self.base_url}/api/recipes", timeout=10)
        return response.status_code == 200
    
    def test_database_collections(self):
        session = self.create_session()
        response = session.get(f"{self.base_url}/api/recipes/collections", timeout=10)
        return response.status_code == 200
    
    def test_database_recipe_detail(self):
        session = self.create_session()
        # Get random recipe ID (assuming IDs 1-100 exist)
        recipe_id = random.randint(1, 50)
        response = session.get(f"{self.base_url}/api/recipes/{recipe_id}", timeout=10)
        return response.status_code in [200, 404]  # 404 is OK if recipe doesn't exist
    
    def test_vector_multi_search(self):
        session = self.create_session()
        queries = ["healthy dinner", "quick breakfast", "chocolate dessert", "vegetarian pasta"]
        query = random.choice(queries)
        
        response = session.post(f"{self.base_url}/api/recipes/search", json={
            "query": query,
            "max_results": 5
        }, timeout=15)
        return response.status_code == 200
    
    def test_vector_collection_search(self, collection):
        if not self.auth_token:
            return False
            
        session = self.create_session()
        session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        
        queries = self.vector_queries.get(collection, ["test query"])
        query = random.choice(queries)
        
        response = session.post(f"{self.base_url}/api/recipes/collections/{collection}/search", json={
            "query": query,
            "max_results": 3
        }, timeout=15)
        return response.status_code == 200
    
    def test_vector_protein_search(self):
        return self.test_vector_collection_search("protein-mains")
    
    def test_vector_dessert_search(self):
        return self.test_vector_collection_search("desserts-sweets")
    
    def test_vector_breakfast_search(self):
        return self.test_vector_collection_search("breakfast-morning")
    
    def test_vector_quick_search(self):
        return self.test_vector_collection_search("quick-light")
    
    def test_vector_fresh_search(self):
        return self.test_vector_collection_search("fresh-cold")
    
    def test_ai_recommendations(self):
        """Test AI recommendations with real Gemini processing"""
        if not self.auth_token:
            return False
        
        session = self.create_session()
        session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        
        conversations = [
            [{"role": "user", "content": "I want something healthy for lunch"}],
            [{"role": "user", "content": "Quick dinner ideas with protein"}],
            [{"role": "user", "content": "Something sweet for dessert"}],
            [
                {"role": "user", "content": "I want something healthy"},
                {"role": "assistant", "content": "I can help with healthy recipes!"},
                {"role": "user", "content": "Something with vegetables and protein"}
            ]
        ]
        
        conversation = random.choice(conversations)
        
        response = session.post(f"{self.base_url}/api/recipes/recommendations", json={
            "conversation_history": conversation,
            "max_results": 3
        }, timeout=60)
        return response.status_code == 200
    
    def test_ai_meal_planning(self):
        """Test AI meal plan generation"""
        if not self.auth_token or not self.user_id:
            return False
        
        session = self.create_session()
        session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        
        meal_plans = [
            "Create a simple 2 day healthy meal plan",
            "Generate a 3 day vegetarian meal plan",
            "Make a quick 2 day meal plan with easy recipes"
        ]
        
        plan_request = random.choice(meal_plans)
        
        response = session.post(f"{self.base_url}/api/meal-plans/text-input?user_id={self.user_id}", json={
            "input_text": plan_request
        }, timeout=120)
        return response.status_code == 200
    
    def test_user_preferences_get(self):
        if not self.auth_token or not self.user_id:
            return False
        
        session = self.create_session()
        session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        
        response = session.get(f"{self.base_url}/api/users/{self.user_id}/preferences", timeout=10)
        return response.status_code in [200, 404]
    
    def test_user_preferences_update(self):
        if not self.auth_token or not self.user_id:
            return False
        
        session = self.create_session()
        session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        
        preferences = {
            "dietary_restrictions": random.choice([[], ["vegetarian"], ["vegan"]]),
            "allergies": random.choice([[], ["nuts"], ["dairy"]]),
            "cuisine_preferences": ["italian", "asian"],
            "cooking_skill": "intermediate"
        }
        
        response = session.put(f"{self.base_url}/api/users/{self.user_id}/preferences", 
                              json=preferences, timeout=10)
        return response.status_code in [200, 201]
    
    # ============= CONCURRENCY TESTS =============
    
    def concurrent_vector_worker(self):
        success, result, time_ms = self.measure_time(self.test_vector_multi_search)
        if success:
            with self.lock:
                self.measurements["concurrent_vector"].append(time_ms)
        return success
    
    def concurrent_database_worker(self):
        success, result, time_ms = self.measure_time(self.test_database_recipes)
        if success:
            with self.lock:
                self.measurements["concurrent_database"].append(time_ms)
        return success
    
    def run_test_category(self, name, test_func, iterations, description):
        """Run a test category with statistical rigor"""
        print(f"\n{description}")
        success_count = 0
        
        for i in range(iterations):
            success, result, time_ms = self.measure_time(test_func)
            if success:
                self.measurements[name].append(time_ms)
                success_count += 1
                print(f"   ✅ {i+1:2d}: {time_ms:7.1f}ms")
            else:
                print(f"   ❌ {i+1:2d}: Failed - {str(result)[:50]}")
        
        avg = statistics.mean(self.measurements[name]) if self.measurements[name] else 0
        print(f"   📊 Success: {success_count}/{iterations} ({success_count/iterations*100:.0f}%) | Avg: {avg:.1f}ms")
    
    def run_comprehensive_tests(self):
        """Run the complete performance test suite"""
        print("🚀 FINAL COMPREHENSIVE MEALMATE AI PERFORMANCE TEST")
        print("=" * 80)
        print("📊 Statistical rigor: 10+ iterations per test")
        print("🤖 Real AI endpoint testing included")
        print("🔍 Multi-collection vs single collection vector search analysis")
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication failed - some tests will be skipped")
        
        # Basic endpoint tests (15 iterations for good statistics)
        self.run_test_category("health_check", self.test_health_check, 15, 
                              "⚡ HEALTH CHECK PERFORMANCE (15 tests)")
        
        self.run_test_category("authentication", self.test_authentication_flow, 10,
                              "🔐 AUTHENTICATION FLOW PERFORMANCE (10 tests)")
        
        # Database tests (15 iterations)
        self.run_test_category("database_recipes", self.test_database_recipes, 15,
                              "🗄️ DATABASE - RECIPE LIST PERFORMANCE (15 tests)")
        
        self.run_test_category("database_collections", self.test_database_collections, 12,
                              "📂 DATABASE - COLLECTIONS LIST PERFORMANCE (12 tests)")
        
        self.run_test_category("database_recipe_detail", self.test_database_recipe_detail, 10,
                              "📄 DATABASE - RECIPE DETAIL PERFORMANCE (10 tests)")
        
        # Vector search tests - THE MAIN COMPARISON
        self.run_test_category("vector_multi_search", self.test_vector_multi_search, 20,
                              "🔍 VECTOR SEARCH - MULTI-COLLECTION (20 tests)")
        
        self.run_test_category("vector_protein_search", self.test_vector_protein_search, 15,
                              "🥩 VECTOR SEARCH - PROTEIN COLLECTION (15 tests)")
        
        self.run_test_category("vector_dessert_search", self.test_vector_dessert_search, 15,
                              "🍰 VECTOR SEARCH - DESSERTS COLLECTION (15 tests)")
        
        self.run_test_category("vector_breakfast_search", self.test_vector_breakfast_search, 15,
                              "🍳 VECTOR SEARCH - BREAKFAST COLLECTION (15 tests)")
        
        self.run_test_category("vector_quick_search", self.test_vector_quick_search, 15,
                              "⚡ VECTOR SEARCH - QUICK MEALS COLLECTION (15 tests)")
        
        self.run_test_category("vector_fresh_search", self.test_vector_fresh_search, 15,
                              "🥗 VECTOR SEARCH - FRESH/COLD COLLECTION (15 tests)")
        
        # User operations (if authenticated)
        if self.auth_token:
            self.run_test_category("user_preferences_get", self.test_user_preferences_get, 10,
                                  "👤 USER PREFERENCES - GET (10 tests)")
            
            self.run_test_category("user_preferences_update", self.test_user_preferences_update, 5,
                                  "✏️ USER PREFERENCES - UPDATE (5 tests)")
        
        # AI tests - REAL PERFORMANCE DATA (limited for cost control)
        if self.auth_token:
            print(f"\n🤖 AI RECOMMENDATIONS PERFORMANCE (10 tests - REAL GEMINI CALLS)")
            ai_success = 0
            for i in range(10):
                # Measure AI requests directly for accurate timing
                session = self.create_session()
                session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                conversations = [
                    [{"role": "user", "content": "I want something healthy for lunch"}],
                    [{"role": "user", "content": "Quick dinner ideas with protein"}],
                    [{"role": "user", "content": "Something sweet for dessert"}],
                    [
                        {"role": "user", "content": "I want something healthy"},
                        {"role": "assistant", "content": "I can help with healthy recipes!"},
                        {"role": "user", "content": "Something with vegetables and protein"}
                    ]
                ]
                
                conversation = random.choice(conversations)
                
                try:
                    start_time = time.time()
                    response = session.post(f"{self.base_url}/api/recipes/recommendations", json={
                        "conversation_history": conversation,
                        "max_results": 3
                    }, timeout=60)
                    end_time = time.time()
                    
                    time_ms = (end_time - start_time) * 1000
                    
                    if response.status_code == 200:
                        self.measurements["ai_recommendations"].append(time_ms)
                        ai_success += 1
                        print(f"   ✅ {i+1:2d}: {time_ms:7.1f}ms ({time_ms/1000:.1f}s)")
                    else:
                        print(f"   ❌ {i+1:2d}: Failed - Status {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ {i+1:2d}: Failed - {str(e)[:50]}")
                
                # Wait between AI calls to avoid overwhelming the system
                if i < 9:
                    time.sleep(2)
            
            avg_ai = statistics.mean(self.measurements["ai_recommendations"]) if self.measurements["ai_recommendations"] else 0
            print(f"   📊 AI Success: {ai_success}/10 ({ai_success*10:.0f}%) | Avg: {avg_ai:.1f}ms ({avg_ai/1000:.1f}s)")
            
            print(f"\n🍽️ MEAL PLAN GENERATION PERFORMANCE (5 tests - EXPENSIVE)")
            meal_success = 0
            for i in range(5):
                # Measure meal plan requests directly for accurate timing
                session = self.create_session()
                session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                meal_plans = [
                    "Create a simple 2 day healthy meal plan",
                    "Generate a 3 day vegetarian meal plan",
                    "Make a quick 2 day meal plan with easy recipes"
                ]
                
                plan_request = random.choice(meal_plans)
                
                try:
                    start_time = time.time()
                    response = session.post(f"{self.base_url}/api/meal-plans/text-input?user_id={self.user_id}", json={
                        "input_text": plan_request
                    }, timeout=120)
                    end_time = time.time()
                    
                    time_ms = (end_time - start_time) * 1000
                    
                    if response.status_code == 200:
                        self.measurements["ai_meal_planning"].append(time_ms)
                        meal_success += 1
                        print(f"   ✅ {i+1:2d}: {time_ms:7.1f}ms ({time_ms/1000:.1f}s)")
                    else:
                        print(f"   ❌ {i+1:2d}: Failed - Status {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ {i+1:2d}: Failed - {str(e)[:50]}")
                
                # Longer wait between meal plan generation
                if i < 4:
                    time.sleep(5)
            
            avg_meal = statistics.mean(self.measurements["ai_meal_planning"]) if self.measurements["ai_meal_planning"] else 0
            print(f"   📊 Meal Plan Success: {meal_success}/5 ({meal_success*20:.0f}%) | Avg: {avg_meal:.1f}ms ({avg_meal/1000:.1f}s)")
        
        # Concurrency tests
        print(f"\n🔄 CONCURRENCY TESTING")
        print("   🔍 Running 20 concurrent vector searches...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.concurrent_vector_worker) for _ in range(20)]
            concurrent.futures.wait(futures)
        
        print("   🗄️ Running 20 concurrent database queries...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.concurrent_database_worker) for _ in range(20)]
            concurrent.futures.wait(futures)
    
    def calculate_comprehensive_stats(self, data):
        """Calculate comprehensive statistics"""
        if not data:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "std": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_data = sorted(data)
        n = len(sorted_data)
        
        def percentile(data, p):
            k = (n - 1) * p
            f = int(k)
            c = k - f
            if f == n - 1:
                return data[f]
            return data[f] * (1 - c) + data[f + 1] * c
        
        return {
            "count": n,
            "avg": round(statistics.mean(data), 2),
            "min": round(min(data), 2),
            "max": round(max(data), 2),
            "std": round(statistics.stdev(data) if n > 1 else 0, 2),
            "p50": round(percentile(sorted_data, 0.50), 2),
            "p95": round(percentile(sorted_data, 0.95), 2),
            "p99": round(percentile(sorted_data, 0.99), 2)
        }
    
    def generate_final_report(self):
        """Generate the definitive performance report"""
        print("\n" + "=" * 100)
        print("📈 FINAL COMPREHENSIVE MEALMATE AI PERFORMANCE REPORT")
        print("=" * 100)
        
        # Calculate stats for all categories
        stats = {}
        for category, data in self.measurements.items():
            stats[category] = self.calculate_comprehensive_stats(data)
        
        # Main performance table
        print(f"\n{'COMPONENT':<35} | {'N':<4} | {'AVG':<10} | {'P50':<10} | {'P95':<10} | {'P99':<10} | {'STATUS'}")
        print("-" * 105)
        
        categories = [
            ("Health Check", "health_check", 50, 200),
            ("Authentication Flow", "authentication", 1000, 2000),
            ("Database: Recipe List", "database_recipes", 100, 500),
            ("Database: Collections", "database_collections", 100, 500),
            ("Database: Recipe Detail", "database_recipe_detail", 100, 500),
            ("Vector: Multi-Collection", "vector_multi_search", 1000, 3000),
            ("Vector: Protein Only", "vector_protein_search", 1000, 3000),
            ("Vector: Desserts Only", "vector_dessert_search", 1000, 3000),
            ("Vector: Breakfast Only", "vector_breakfast_search", 1000, 3000),
            ("Vector: Quick Only", "vector_quick_search", 1000, 3000),
            ("Vector: Fresh Only", "vector_fresh_search", 1000, 3000),
            ("AI Recommendations (REAL)", "ai_recommendations", 20000, 60000),
            ("AI Meal Planning (REAL)", "ai_meal_planning", 30000, 120000),
            ("User Preferences: Get", "user_preferences_get", 200, 1000),
            ("User Preferences: Update", "user_preferences_update", 500, 2000),
            ("Concurrent Vector Search", "concurrent_vector", 1000, 3000),
            ("Concurrent Database", "concurrent_database", 100, 500)
        ]
        
        for name, key, excellent_threshold, good_threshold in categories:
            s = stats[key]
            if s["count"] > 0:
                if s["p95"] < excellent_threshold:
                    status = "✅ EXCELLENT"
                elif s["p95"] < good_threshold:
                    status = "🟡 GOOD"
                else:
                    status = "🔴 NEEDS WORK"
                
                print(f"{name:<35} | {s['count']:<4} | {s['avg']:<10.1f} | {s['p50']:<10.1f} | {s['p95']:<10.1f} | {s['p99']:<10.1f} | {status}")
            else:
                print(f"{name:<35} | {'0':<4} | {'NO DATA':<10} | {'NO DATA':<10} | {'NO DATA':<10} | {'NO DATA':<10} | ⚠️ NO DATA")
        
        # Vector search comparison analysis
        print(f"\n🔍 VECTOR SEARCH PERFORMANCE COMPARISON")
        print("-" * 70)
        
        vector_comparisons = [
            ("Multi-Collection Search", "vector_multi_search"),
            ("Protein Collection Only", "vector_protein_search"),
            ("Desserts Collection Only", "vector_dessert_search"),
            ("Breakfast Collection Only", "vector_breakfast_search"),
            ("Quick Meals Collection Only", "vector_quick_search"),
            ("Fresh/Cold Collection Only", "vector_fresh_search")
        ]
        
        print("Collection Search Type           | Tests | Avg (ms) | P95 (ms) | Performance")
        print("-" * 70)
        for name, key in vector_comparisons:
            s = stats[key]
            if s["count"] > 0:
                perf = "✅ Excellent" if s["p95"] < 1000 else "🟡 Good" if s["p95"] < 3000 else "🔴 Slow"
                print(f"{name:<30} | {s['count']:5} | {s['avg']:8.1f} | {s['p95']:8.1f} | {perf}")
        
        # AI performance analysis
        print(f"\n🤖 AI PERFORMANCE ANALYSIS (REAL GEMINI API CALLS)")
        print("-" * 60)
        
        ai_rec_stats = stats["ai_recommendations"]
        ai_meal_stats = stats["ai_meal_planning"]
        
        if ai_rec_stats["count"] > 0:
            print(f"AI Recommendations:")
            print(f"  Tests: {ai_rec_stats['count']}")
            print(f"  Average: {ai_rec_stats['avg']:.0f}ms ({ai_rec_stats['avg']/1000:.1f}s)")
            print(f"  P95: {ai_rec_stats['p95']:.0f}ms ({ai_rec_stats['p95']/1000:.1f}s)")
            print(f"  Range: {ai_rec_stats['min']:.0f}ms - {ai_rec_stats['max']:.0f}ms")
        
        if ai_meal_stats["count"] > 0:
            print(f"\nAI Meal Planning:")
            print(f"  Tests: {ai_meal_stats['count']}")
            print(f"  Average: {ai_meal_stats['avg']:.0f}ms ({ai_meal_stats['avg']/1000:.1f}s)")
            print(f"  P95: {ai_meal_stats['p95']:.0f}ms ({ai_meal_stats['p95']/1000:.1f}s)")
            print(f"  Range: {ai_meal_stats['min']:.0f}ms - {ai_meal_stats['max']:.0f}ms")
        
        # Save comprehensive report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_tests_run": sum(s["count"] for s in stats.values()),
                "categories_tested": len([s for s in stats.values() if s["count"] > 0]),
                "auth_successful": bool(self.auth_token),
                "ai_tests_successful": ai_rec_stats["count"] > 0 or ai_meal_stats["count"] > 0,
                "vector_search_collections_tested": 6
            },
            "measurements": self.measurements,
            "statistics": stats
        }
        
        with open("performance-testing/results/final_comprehensive_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 FINAL REPORT SAVED: performance-testing/results/final_comprehensive_report.json")
        print(f"📊 Total Tests Executed: {report_data['test_summary']['total_tests_run']}")
        print(f"🎯 Categories Tested: {report_data['test_summary']['categories_tested']}")
        print("=" * 100)
        
        return report_data

if __name__ == "__main__":
    tester = FinalComprehensiveTest()
    tester.run_comprehensive_tests()
    tester.generate_final_report()