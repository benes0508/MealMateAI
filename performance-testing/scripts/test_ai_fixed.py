#!/usr/bin/env python3.9
"""
Test AI Endpoints with Valid Token (fixed indentation)
"""

import requests
import time
import json
import uuid

def test_ai_endpoints():
    """Test AI endpoints with proper authentication"""
    
    print("🔍 TESTING AI ENDPOINTS")
    print("="*50)
    
    # Setup
    base_url = "http://localhost:3000"
    user_service_url = "http://localhost:8000"
    
    # Create unique user
    test_email = f"ai_test_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123"
    
    print("1️⃣ Getting authentication token...")
    
    try:
        # Register (ignore if exists)
        register_response = requests.post(f"{user_service_url}/users/register/simple", json={
            "email": test_email,
            "password": password,
            "name": "AI Test User"
        }, timeout=10)
        
        print(f"   Register: {register_response.status_code}")
        
        # Login
        login_response = requests.post(f"{user_service_url}/users/login/json", json={
            "email": test_email,
            "password": password
        }, timeout=10)
        
        print(f"   Login: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        # Get token
        data = login_response.json()
        auth_token = data.get("token", data.get("access_token"))
        user_data = data.get("user", {})
        user_id = user_data.get("id")
        
        print(f"   ✅ Got token! User ID: {user_id}")
        
        # Setup session
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}",
            "x-bypass-rate-limit": "true"
        })
        
        # Test AI recommendations
        print(f"\n2️⃣ Testing AI Recommendations...")
        
        start_time = time.time()
        
        response = session.post(f"{base_url}/api/recipes/recommendations", json={
            "conversation_history": [
                {"role": "user", "content": "I want something healthy for lunch"},
                {"role": "assistant", "content": "I can help with healthy lunch ideas!"},
                {"role": "user", "content": "Something with vegetables and protein"}
            ],
            "max_results": 3
        }, timeout=60)
        
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        
        print(f"   Status: {response.status_code}")
        print(f"   Duration: {duration:.0f}ms ({duration/1000:.1f}s)")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                
                recommendations = response_data.get('recommendations', [])
                query_analysis = response_data.get('query_analysis', {})
                
                print(f"   ✅ SUCCESS!")
                print(f"   📊 Recommendations: {len(recommendations)}")
                
                if query_analysis:
                    ai_time = query_analysis.get('processing_time_ms', 0)
                    print(f"   🤖 AI Processing: {ai_time}ms ({ai_time/1000:.1f}s)")
                    print(f"   🧠 Collections: {len(query_analysis.get('collections_searched', []))}")
                    print(f"   🎯 Generated Queries: {len(query_analysis.get('generated_queries', {}))}")
                    
                    if ai_time > 3000:
                        print(f"   ✅ AI processing time indicates real Gemini calls")
                    else:
                        print(f"   ⚠️  AI processing time seems low ({ai_time}ms)")
                        
                    # Show sample generated queries
                    generated = query_analysis.get('generated_queries', {})
                    if generated:
                        print(f"   🤖 Sample Generated Queries:")
                        for collection, queries in list(generated.items())[:2]:
                            print(f"      {collection}: {queries}")
                else:
                    print(f"   ❌ No query analysis found")
                
                # Show first recommendation
                if recommendations:
                    rec = recommendations[0]
                    print(f"   📄 Sample Recommendation:")
                    print(f"      Title: {rec.get('title', 'N/A')}")
                    print(f"      Collection: {rec.get('collection', 'N/A')}")
                    print(f"      Similarity: {rec.get('similarity_score', 'N/A')}")
                    
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
        
        # Test meal plan generation
        print(f"\n3️⃣ Testing Meal Plan Generation...")
        
        start_time = time.time()
        
        response = session.post(f"{base_url}/api/meal-plans/text-input?user_id={user_id}", json={
            "input_text": "Create a simple 2 day healthy meal plan"
        }, timeout=120)
        
        end_time = time.time()
        duration = (end_time - start_time) * 1000
        
        print(f"   Status: {response.status_code}")
        print(f"   Duration: {duration:.0f}ms ({duration/1000:.1f}s)")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"   ✅ Meal plan generated!")
            print(f"   📋 Plan ID: {response_data.get('id', 'N/A')}")
            
            if duration > 10000:
                print(f"   ✅ Generation time indicates real AI processing")
            else:
                print(f"   ⚠️  Generation time seems low for AI")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n" + "="*50)
    print("🎯 REAL AI PERFORMANCE SUMMARY")
    print("="*50)
    print("✅ Valid AI: > 5s processing with query analysis")
    print("⚠️  Suspect: < 3s or missing AI data")
    print("❌ Failed: HTTP errors")

if __name__ == "__main__":
    test_ai_endpoints()