#!/usr/bin/env python3.9
"""
Test AI Endpoints with Valid Token (bypassing auth issues)
Use a token from the successful performance test to validate AI responses
"""

import requests
import time
import json

def test_ai_with_existing_token():
    """Test AI endpoints using a token that we know works"""
    
    print("🔍 TESTING AI ENDPOINTS WITH EXISTING TOKEN")
    print("="*60)
    
    # First, let's create a fresh user and get a token
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "x-bypass-rate-limit": "true"
    })
    
    base_url = "http://localhost:3000"
    
    # Try to get a working token by hitting the endpoint differently
    print("1️⃣ Attempting direct user service access...")
    
    # Try calling user service directly (port 8000)
    try:
        import uuid
        user_service_url = "http://localhost:8000"
        
        # Use unique email to avoid conflicts
        test_email = f"ai_test_{uuid.uuid4().hex[:8]}@test.com"
        password = "TestPass123"
        
        # Try registering directly with user service
        register_response = requests.post(f"{user_service_url}/users/register/simple", json={
            "email": test_email,
            "password": password,
            "name": "AI Test User"
        }, timeout=10)
        
        print(f"   Direct user service register: {register_response.status_code}")
        
        # Always try login regardless of register result (user might exist)
        login_response = requests.post(f"{user_service_url}/users/login/json", json={
            "email": test_email,
            "password": password
        }, timeout=10)
        
        print(f"   Direct user service login: {login_response.status_code}")
        
        if login_response.status_code == 200:
            data = login_response.json()
            auth_token = data.get("token", data.get("access_token"))
            user_data = data.get("user", {})
            user_id = user_data.get("id")
            
            print(f"   ✅ Got token directly from user service!")
            print(f"   User ID: {user_id}")
            
            # Now test AI with this token via API gateway
            session.headers.update({"Authorization": f"Bearer {auth_token}"})
            
            # Test AI recommendations
            print(f"\n2️⃣ Testing AI Recommendations...")
            
                test_cases = [
                    {
                        "name": "Simple Request",
                        "conversation": [{"role": "user", "content": "I want something healthy"}],
                    },
                    {
                        "name": "Detailed Request",
                        "conversation": [
                            {"role": "user", "content": "I want something healthy for lunch"},
                            {"role": "assistant", "content": "I can help with healthy lunch ideas!"},
                            {"role": "user", "content": "Something with vegetables and protein"}
                        ],
                    }
                ]
                
                for i, test_case in enumerate(test_cases, 1):
                    print(f"\n   Test {i}: {test_case['name']}")
                    
                    start_time = time.time()
                    
                    try:
                        response = session.post(f"{base_url}/api/recipes/recommendations", json={
                            "conversation_history": test_case["conversation"],
                            "max_results": 3
                        }, timeout=60)
                        
                        end_time = time.time()
                        duration = (end_time - start_time) * 1000
                        
                        print(f"   Status: {response.status_code}")
                        print(f"   Duration: {duration:.0f}ms ({duration/1000:.1f}s)")
                        
                        if response.status_code == 200:
                            try:
                                response_data = response.json()
                                
                                # Detailed analysis
                                recommendations = response_data.get('recommendations', [])
                                query_analysis = response_data.get('query_analysis', {})
                                
                                print(f"   ✅ SUCCESS")
                                print(f"   📊 Recommendations: {len(recommendations)}")
                                
                                if query_analysis:
                                    ai_processing_time = query_analysis.get('processing_time_ms', 0)
                                    print(f"   🤖 AI Processing Time: {ai_processing_time}ms ({ai_processing_time/1000:.1f}s)")
                                    print(f"   🧠 Collections Searched: {len(query_analysis.get('collections_searched', []))}")
                                    print(f"   🎯 Generated Queries: {len(query_analysis.get('generated_queries', {}))}")
                                    print(f"   🔍 Detected Preferences: {query_analysis.get('detected_preferences', [])}")
                                    
                                    # Validate if this looks like real AI processing
                                    if ai_processing_time > 1000:
                                        print(f"   ✅ AI processing time suggests real Gemini calls")
                                    else:
                                        print(f"   ⚠️  AI processing time seems too fast ({ai_processing_time}ms)")
                                    
                                    # Show generated queries to validate AI
                                    generated_queries = query_analysis.get('generated_queries', {})
                                    if generated_queries:
                                        print(f"   🤖 Sample Generated Queries:")
                                        for collection, queries in list(generated_queries.items())[:2]:
                                            print(f"      {collection}: {queries}")
                                else:
                                    print(f"   ❌ No query analysis - AI may not be working")
                                
                                # Show first recommendation
                                if recommendations:
                                    rec = recommendations[0]
                                    print(f"   📄 Sample Recommendation:")
                                    print(f"      Title: {rec.get('title', 'N/A')}")
                                    print(f"      Collection: {rec.get('collection', 'N/A')}")
                                    print(f"      Similarity: {rec.get('similarity_score', 'N/A')}")
                                    
                            except json.JSONDecodeError:
                                print(f"   ❌ Invalid JSON response")
                                print(f"   Raw response: {response.text[:300]}")
                        else:
                            print(f"   ❌ Failed: {response.status_code}")
                            print(f"   Error: {response.text[:200]}")
                    
                    except requests.exceptions.Timeout:
                        print(f"   ⏰ Request timed out")
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
                    
                    # Wait between tests
                    if i < len(test_cases):
                        time.sleep(2)
                
                # Test meal plan generation
                print(f"\n3️⃣ Testing Meal Plan Generation...")
                
                start_time = time.time()
                try:
                    response = session.post(f"{base_url}/api/meal-plans/text-input", json={
                        "user_id": user_id,
                        "input_text": "Create a simple 2 day meal plan with healthy recipes"
                    }, timeout=120)
                    
                    end_time = time.time()
                    duration = (end_time - start_time) * 1000
                    
                    print(f"   Status: {response.status_code}")
                    print(f"   Duration: {duration:.0f}ms ({duration/1000:.1f}s)")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        print(f"   ✅ Meal plan generated")
                        print(f"   📋 Meal Plan ID: {response_data.get('id', 'N/A')}")
                        
                        if duration > 5000:
                            print(f"   ✅ Generation time suggests real AI processing")
                        else:
                            print(f"   ⚠️  Generation time suspiciously fast")
                    else:
                        print(f"   ❌ Failed: {response.status_code}")
                        print(f"   Error: {response.text[:200]}")
                        
                except requests.exceptions.Timeout:
                    print(f"   ⏰ Request timed out")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                
            else:
                print(f"   ❌ Direct login failed: {login_response.text}")
        else:
            print(f"   ❌ Direct registration failed: {register_response.text}")
            
    except Exception as e:
        print(f"   ❌ Direct user service access failed: {e}")
    
    print(f"\n" + "="*60)
    print("🎯 VALIDATION SUMMARY")
    print("="*60)
    print("✅ Valid AI: Processing times > 3s with query analysis and generated queries")
    print("⚠️  Suspect: Fast responses < 1s or missing AI-specific data")
    print("❌ Failed: HTTP errors or timeouts")

if __name__ == "__main__":
    test_ai_with_existing_token()