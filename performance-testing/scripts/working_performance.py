#!/usr/bin/env python3.9
"""
Working Performance Test for MealMateAI
Focus on endpoints that work reliably with proper authentication flow
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

class WorkingPerformanceTester:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.auth_token = None
        self.user_id = None
        self.measurements = {
            "health_check": [],
            "authentication": [],
            "database_recipes": [],
            "database_collections": [],
            "vector_multi_search": [],
            "vector_protein_search": [],
            "vector_dessert_search": [],
            "vector_breakfast_search": [],
            "vector_quick_search": [],
            "ai_recommendations": [],
            "concurrent_vector": [],
            "concurrent_database": []
        }
        self.lock = Lock()
    
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
    
    def authenticate_once(self):
        """Authenticate once for all tests"""
        session = self.create_session()
        email = f"working_test_{uuid.uuid4().hex[:6]}@test.com"
        password = "TestPass123"
        
        print(f"🔐 Authenticating as {email}...")
        
        try:
            # Register
            register_response = session.post(f"{self.base_url}/api/users/register", json={
                "email": email,
                "password": password,
                "name": "Working Performance Test User"
            }, timeout=10)
            
            print(f"   Register: {register_response.status_code}")
            
            # Always try login (even if register failed with 409 - user exists)
            login_response = session.post(f"{self.base_url}/api/users/login", json={
                "email": email,
                "password": password
            }, timeout=10)
            
            print(f"   Login: {login_response.status_code}")
            
            if login_response.status_code == 200:
                data = login_response.json()
                self.auth_token = data.get("token", data.get("access_token"))
                user_data = data.get("user", {})
                self.user_id = user_data.get("id")
                print(f"   ✅ Success! Token: {bool(self.auth_token)}, User ID: {self.user_id}")
                return True
            else:
                print(f"   ❌ Login failed: {login_response.text[:100]}")
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
        email = f"auth_flow_{uuid.uuid4().hex[:4]}@test.com"
        password = "TestPass123"
        session = self.create_session()
        
        # Register
        register_response = session.post(f"{self.base_url}/api/users/register", json={
            "email": email,
            "password": password,
            "name": "Auth Flow Test"
        }, timeout=10)
        
        # Login regardless of register result
        login_response = session.post(f"{self.base_url}/api/users/login", json={
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
    
    def test_vector_multi_search(self):
        session = self.create_session()
        queries = ["healthy dinner", "quick breakfast", "chocolate dessert"]
        query = random.choice(queries)
        
        response = session.post(f"{self.base_url}/api/recipes/search", json={
            "query": query,
            "max_results": 5
        }, timeout=15)
        return response.status_code == 200
    
    def test_vector_protein_search(self):
        session = self.create_session()
        queries = ["grilled chicken", "beef steak", "salmon fillet"]
        query = random.choice(queries)
        
        response = session.post(f"{self.base_url}/api/recipes/collections/protein-mains/search", json={
            "query": query,
            "max_results": 3
        }, timeout=15)
        return response.status_code == 200
    
    def test_vector_dessert_search(self):
        session = self.create_session()
        queries = ["chocolate cake", "vanilla ice cream", "apple pie"]
        query = random.choice(queries)
        
        response = session.post(f"{self.base_url}/api/recipes/collections/desserts-sweets/search", json={
            "query": query,
            "max_results": 3
        }, timeout=15)
        return response.status_code == 200
    
    def test_vector_breakfast_search(self):
        session = self.create_session()
        queries = ["pancakes", "scrambled eggs", "oatmeal"]
        query = random.choice(queries)
        
        response = session.post(f"{self.base_url}/api/recipes/collections/breakfast-morning/search", json={
            "query": query,
            "max_results": 3
        }, timeout=15)
        return response.status_code == 200
    
    def test_vector_quick_search(self):
        session = self.create_session()
        queries = ["15 minute meals", "quick salad", "fast pasta"]
        query = random.choice(queries)
        
        response = session.post(f"{self.base_url}/api/recipes/collections/quick-light/search", json={
            "query": query,
            "max_results": 3
        }, timeout=15)
        return response.status_code == 200
    
    def test_ai_recommendations(self):
        """Test AI recommendations with authentication"""
        if not self.auth_token:
            return False
        
        session = self.create_session()
        session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        
        conversations = [
            [{"role": "user", "content": "I want something healthy"}],
            [{"role": "user", "content": "Quick dinner ideas"}],
            [{"role": "user", "content": "Something sweet"}]
        ]
        
        conversation = random.choice(conversations)
        
        response = session.post(f"{self.base_url}/api/recipes/recommendations", json={
            "conversation_history": conversation,
            "max_results": 3
        }, timeout=30)
        return response.status_code == 200
    
    # ============= CONCURRENT TESTS =============
    
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
    
    def run_category(self, name, test_func, iterations, description):
        """Run a test category"""
        print(f"\n{description}")
        success_count = 0
        
        for i in range(iterations):
            success, result, time_ms = self.measure_time(test_func)
            if success:
                self.measurements[name].append(time_ms)
                success_count += 1
                print(f"   ✅ {i+1:2d}: {time_ms:7.2f}ms")
            else:
                print(f"   ❌ {i+1:2d}: Failed - {str(result)[:50]}")
        
        avg = statistics.mean(self.measurements[name]) if self.measurements[name] else 0
        print(f"   📊 Success: {success_count}/{iterations} ({success_count/iterations*100:.0f}%) | Avg: {avg:.1f}ms")
    
    def run_tests(self):
        """Run all performance tests"""
        print("🚀 WORKING MEALMATE AI PERFORMANCE TESTING")
        print("=" * 70)
        
        # Authenticate once
        if not self.authenticate_once():
            print("❌ Authentication failed - AI tests will be skipped")
        
        # Basic tests
        self.run_category("health_check", self.test_health_check, 20, 
                         "⚡ Health Check Performance (20 tests)")
        
        self.run_category("authentication", self.test_authentication_flow, 8,
                         "🔐 Authentication Flow Performance (8 tests)")
        
        # Database tests
        self.run_category("database_recipes", self.test_database_recipes, 20,
                         "🗄️ Database - Recipe List Performance (20 tests)")
        
        self.run_category("database_collections", self.test_database_collections, 15,
                         "📂 Database - Collections List Performance (15 tests)")
        
        # Vector search tests - the main comparison you wanted
        self.run_category("vector_multi_search", self.test_vector_multi_search, 25,
                         "🔍 Vector Search - Multi-Collection (25 tests)")
        
        self.run_category("vector_protein_search", self.test_vector_protein_search, 20,
                         "🥩 Vector Search - Protein Collection (20 tests)")
        
        self.run_category("vector_dessert_search", self.test_vector_dessert_search, 20,
                         "🍰 Vector Search - Desserts Collection (20 tests)")
        
        self.run_category("vector_breakfast_search", self.test_vector_breakfast_search, 20,
                         "🍳 Vector Search - Breakfast Collection (20 tests)")
        
        self.run_category("vector_quick_search", self.test_vector_quick_search, 20,
                         "⚡ Vector Search - Quick Meals Collection (20 tests)")
        
        # AI tests (limited)
        if self.auth_token:
            print(f"\n🤖 AI Recommendations Testing (3 attempts - COSTS MONEY)")
            ai_success = 0
            for i in range(3):
                success, result, time_ms = self.measure_time(self.test_ai_recommendations)
                if success:
                    self.measurements["ai_recommendations"].append(time_ms)
                    ai_success += 1
                    print(f"   ✅ {i+1}: {time_ms:7.2f}ms")
                else:
                    print(f"   ❌ {i+1}: Failed - {str(result)[:50]}")
                
                if i < 2:
                    time.sleep(2)  # Wait between AI calls
            
            print(f"   📊 AI Success: {ai_success}/3")
        
        # Concurrent tests
        print(f"\n🔄 Concurrent Performance Testing")
        print("-" * 40)
        
        # Concurrent vector search
        print("   🔍 Running 15 concurrent vector searches...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.concurrent_vector_worker) for _ in range(15)]
            concurrent.futures.wait(futures)
        
        # Concurrent database
        print("   🗄️ Running 15 concurrent database queries...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.concurrent_database_worker) for _ in range(15)]
            concurrent.futures.wait(futures)
    
    def calculate_stats(self, data):
        """Calculate comprehensive statistics"""
        if not data:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "p50": 0, "p95": 0, "p99": 0}
        
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
            "p50": round(percentile(sorted_data, 0.50), 2),
            "p95": round(percentile(sorted_data, 0.95), 2),
            "p99": round(percentile(sorted_data, 0.99), 2)
        }
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 80)
        print("📈 MEALMATE AI PERFORMANCE REPORT")
        print("=" * 80)
        
        # Calculate stats
        stats = {}
        for category, data in self.measurements.items():
            stats[category] = self.calculate_stats(data)
        
        # Performance summary table
        print(f"\n{'ENDPOINT':<30} | {'N':<4} | {'AVG':<8} | {'P50':<8} | {'P95':<8} | {'MIN':<8} | {'MAX':<8}")
        print("-" * 80)
        
        categories = [
            ("Health Check", "health_check"),
            ("Authentication", "authentication"),
            ("DB: Recipe List", "database_recipes"),
            ("DB: Collections", "database_collections"),
            ("Vector: Multi-Collection", "vector_multi_search"),
            ("Vector: Protein Only", "vector_protein_search"),
            ("Vector: Desserts Only", "vector_dessert_search"),
            ("Vector: Breakfast Only", "vector_breakfast_search"),
            ("Vector: Quick Only", "vector_quick_search"),
            ("AI Recommendations", "ai_recommendations"),
            ("Concurrent Vector", "concurrent_vector"),
            ("Concurrent Database", "concurrent_database")
        ]
        
        for name, key in categories:
            s = stats[key]
            if s["count"] > 0:
                print(f"{name:<30} | {s['count']:<4} | {s['avg']:<8.1f} | {s['p50']:<8.1f} | {s['p95']:<8.1f} | {s['min']:<8.1f} | {s['max']:<8.1f}")
            else:
                print(f"{name:<30} | {'0':<4} | {'NO DATA'}")
        
        # Vector search comparison analysis
        print(f"\n🔍 VECTOR SEARCH PERFORMANCE COMPARISON")
        print("-" * 50)
        
        vector_comparisons = [
            ("Multi-Collection Search", "vector_multi_search"),
            ("Protein Collection Only", "vector_protein_search"),
            ("Desserts Collection Only", "vector_dessert_search"),
            ("Breakfast Collection Only", "vector_breakfast_search"),
            ("Quick Meals Collection Only", "vector_quick_search")
        ]
        
        for name, key in vector_comparisons:
            s = stats[key]
            if s["count"] > 0:
                print(f"{name:<25}: Avg={s['avg']:6.1f}ms | P95={s['p95']:6.1f}ms | Tests={s['count']}")
        
        # Performance assessment
        print(f"\n🎯 PERFORMANCE ASSESSMENT")
        print("-" * 40)
        
        assessments = [
            ("Health Check", "health_check", 50, 200),
            ("Database Queries", "database_recipes", 100, 500),
            ("Vector Search", "vector_multi_search", 1000, 3000),
            ("AI Recommendations", "ai_recommendations", 5000, 15000)
        ]
        
        for name, key, excellent, good in assessments:
            s = stats[key]
            if s["count"] > 0:
                if s["p95"] < excellent:
                    status = "✅ EXCELLENT"
                elif s["p95"] < good:
                    status = "🟡 GOOD"
                else:
                    status = "🔴 NEEDS IMPROVEMENT"
                
                print(f"{name:<20}: {status} (P95: {s['p95']:6.1f}ms)")
            else:
                print(f"{name:<20}: ⚠️ NO DATA")
        
        # Save results
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": sum(s["count"] for s in stats.values()),
                "auth_successful": bool(self.auth_token),
                "ai_tests_run": stats["ai_recommendations"]["count"] > 0
            },
            "measurements": self.measurements,
            "statistics": stats
        }
        
        with open("performance-testing/results/working_performance_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Report saved: performance-testing/results/working_performance_report.json")
        print(f"📊 Total tests: {report_data['summary']['total_tests']}")
        print("=" * 80)

if __name__ == "__main__":
    tester = WorkingPerformanceTester()
    tester.run_tests()
    tester.generate_report()