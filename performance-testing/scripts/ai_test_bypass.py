#!/usr/bin/env python3.9
"""
AI Performance Test with Direct User Service Authentication
Bypasses API Gateway rate limiting completely
"""

import requests
import time
import json
import uuid
import statistics

def test_ai_performance_direct():
    """Test AI endpoints bypassing API gateway rate limiting"""
    
    print("🔍 AI PERFORMANCE TEST (Direct User Service)")
    print("="*60)
    
    base_url = "http://localhost:3000"
    user_service_url = "http://localhost:8000"
    
    # Create unique user
    test_email = f"ai_perf_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123"
    
    print("1️⃣ Getting authentication token...")
    
    try:
        # Register user
        register_response = requests.post(f"{user_service_url}/users/register/simple", json={
            "email": test_email,
            "password": password,
            "name": "AI Performance Test User"
        }, timeout=10)
        
        # Login to get token
        login_response = requests.post(f"{user_service_url}/users/login/json", json={
            "email": test_email,
            "password": password
        }, timeout=10)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        data = login_response.json()
        auth_token = data.get("token", data.get("access_token"))
        user_data = data.get("user", {})
        user_id = user_data.get("id")
        
        print(f"   ✅ Got token! User ID: {user_id}")
        
        # Setup session with bypass headers
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}",
            "x-bypass-rate-limit": "true"
        })
        
        # Test AI recommendations (10 iterations)
        print(f"\n2️⃣ Testing AI Recommendations (10 iterations)...")
        recommendation_times = []
        
        for i in range(10):
            start_time = time.time()
            
            response = session.post(f"{base_url}/api/recipes/recommendations", json={
                "conversation_history": [
                    {"role": "user", "content": f"I want something healthy for test {i+1}"},
                    {"role": "assistant", "content": "I can help with healthy ideas!"},
                    {"role": "user", "content": "Something with vegetables and protein"}
                ],
                "max_results": 3
            }, timeout=60)
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                recommendation_times.append(duration_ms)
                print(f"   ✅ {i+1:2d}: {duration_ms:7.1f}ms ({duration_ms/1000:.1f}s)")
                
                # Validate AI response
                try:
                    response_data = response.json()
                    query_analysis = response_data.get('query_analysis', {})
                    ai_processing_time = query_analysis.get('processing_time_ms', 0)
                    if ai_processing_time > 1000:
                        print(f"      🤖 AI Processing: {ai_processing_time}ms - VALID")
                    else:
                        print(f"      ⚠️  AI Processing: {ai_processing_time}ms - TOO FAST")
                except:
                    print(f"      ❌ No AI analysis data")
            else:
                print(f"   ❌ {i+1:2d}: Failed with {response.status_code} - {response.text[:100]}")
            
            # Small delay between requests
            time.sleep(1)
        
        # Test meal plan generation (5 iterations)
        print(f"\n3️⃣ Testing Meal Plan Generation (5 iterations)...")
        meal_plan_times = []
        
        for i in range(5):
            start_time = time.time()
            
            response = session.post(f"{base_url}/api/meal-plans/text-input?user_id={user_id}", json={
                "input_text": f"Create a simple 2 day healthy meal plan test {i+1}"
            }, timeout=120)
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                meal_plan_times.append(duration_ms)
                print(f"   ✅ {i+1:2d}: {duration_ms:7.1f}ms ({duration_ms/1000:.1f}s)")
            else:
                print(f"   ❌ {i+1:2d}: Failed with {response.status_code} - {response.text[:100]}")
            
            # Small delay between requests
            time.sleep(2)
        
        # Statistics
        print(f"\n" + "="*60)
        print(f"📊 AI PERFORMANCE RESULTS")
        print(f"="*60)
        
        if recommendation_times:
            rec_avg = statistics.mean(recommendation_times)
            rec_median = statistics.median(recommendation_times)
            rec_min = min(recommendation_times)
            rec_max = max(recommendation_times)
            print(f"AI Recommendations ({len(recommendation_times)} tests):")
            print(f"   Average: {rec_avg:7.1f}ms ({rec_avg/1000:.1f}s)")
            print(f"   Median:  {rec_median:7.1f}ms ({rec_median/1000:.1f}s)")
            print(f"   Range:   {rec_min:7.1f}ms - {rec_max:7.1f}ms")
        
        if meal_plan_times:
            plan_avg = statistics.mean(meal_plan_times)
            plan_median = statistics.median(meal_plan_times)
            plan_min = min(meal_plan_times)
            plan_max = max(meal_plan_times)
            print(f"\nMeal Plan Generation ({len(meal_plan_times)} tests):")
            print(f"   Average: {plan_avg:7.1f}ms ({plan_avg/1000:.1f}s)")
            print(f"   Median:  {plan_median:7.1f}ms ({plan_median/1000:.1f}s)")
            print(f"   Range:   {plan_min:7.1f}ms - {plan_max:7.1f}ms")
        
        print(f"\n✅ Performance test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_ai_performance_direct()