#!/usr/bin/env python3.9
"""
Debug AI Recommendations Response Validity
Check if AI endpoints are actually calling Gemini or just failing fast
"""

import requests
import time
import json
import uuid

def test_ai_recommendation_validity():
    """Test if AI recommendations are actually calling Gemini and returning valid responses"""
    
    print("🔍 DEBUGGING AI RECOMMENDATION VALIDITY")
    print("="*60)
    
    # Setup session
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "x-bypass-rate-limit": "true"
    })
    
    base_url = "http://localhost:3000"
    
    # First authenticate
    print("1️⃣ Authenticating...")
    email = f"ai_debug_{uuid.uuid4().hex[:6]}@test.com"
    password = "TestPass123"
    
    try:
        # Register
        register_response = session.post(f"{base_url}/api/users/register", json={
            "email": email,
            "password": password,
            "name": "AI Debug User"
        }, timeout=10)
        
        print(f"   Register status: {register_response.status_code}")
        
        # Login
        login_response = session.post(f"{base_url}/api/users/login", json={
            "email": email,
            "password": password
        }, timeout=10)
        
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Authentication failed: {login_response.text}")
            return
        
        # Get auth token
        data = login_response.json()
        auth_token = data.get("token", data.get("access_token"))
        session.headers.update({"Authorization": f"Bearer {auth_token}"})
        
        print(f"   ✅ Authenticated successfully")
        
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return
    
    # Test AI recommendations with detailed analysis
    print(f"\n2️⃣ Testing AI Recommendations...")
    
    test_conversations = [
        {
            "name": "Simple Request",
            "conversation": [{"role": "user", "content": "I want something healthy for lunch"}],
            "expected_processing_time": "> 3 seconds"
        },
        {
            "name": "Complex Request", 
            "conversation": [
                {"role": "user", "content": "I want something healthy for lunch"},
                {"role": "assistant", "content": "I can help with healthy lunch ideas!"},
                {"role": "user", "content": "Something with vegetables and protein, not too heavy"}
            ],
            "expected_processing_time": "> 5 seconds"
        }
    ]
    
    for i, test_case in enumerate(test_conversations, 1):
        print(f"\n   Test {i}: {test_case['name']}")
        print(f"   Expected: {test_case['expected_processing_time']}")
        
        start_time = time.time()
        
        try:
            response = session.post(f"{base_url}/api/recipes/recommendations", json={
                "conversation_history": test_case["conversation"],
                "max_results": 3
            }, timeout=60)  # Longer timeout for AI
            
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # Convert to ms
            
            print(f"   Status: {response.status_code}")
            print(f"   Duration: {duration:.0f}ms ({duration/1000:.1f}s)")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Analyze response structure
                    print(f"   ✅ Response received")
                    print(f"   Recommendations count: {len(response_data.get('recommendations', []))}")
                    
                    # Check if query analysis exists (indicates AI processing)
                    query_analysis = response_data.get('query_analysis', {})
                    if query_analysis:
                        print(f"   📊 Query Analysis Found:")
                        print(f"      - Processing time: {query_analysis.get('processing_time_ms', 'N/A')}ms")
                        print(f"      - Collections searched: {len(query_analysis.get('collections_searched', []))}")
                        print(f"      - Generated queries: {len(query_analysis.get('generated_queries', {}))}")
                        print(f"      - Detected preferences: {query_analysis.get('detected_preferences', [])}")
                        
                        # Check if this looks like real AI analysis
                        processing_time_ms = query_analysis.get('processing_time_ms', 0)
                        if processing_time_ms > 1000:  # > 1 second indicates likely real AI processing
                            print(f"   ✅ AI processing time reasonable ({processing_time_ms}ms)")
                        else:
                            print(f"   ⚠️ AI processing time suspiciously fast ({processing_time_ms}ms)")
                    else:
                        print(f"   ❌ No query analysis found - may not be using AI")
                    
                    # Show first recommendation for content validation
                    recommendations = response_data.get('recommendations', [])
                    if recommendations:
                        first_rec = recommendations[0]
                        print(f"   📄 First recommendation:")
                        print(f"      - Title: {first_rec.get('title', 'N/A')}")
                        print(f"      - Collection: {first_rec.get('collection', 'N/A')}")
                        print(f"      - Similarity score: {first_rec.get('similarity_score', 'N/A')}")
                        print(f"      - Summary length: {len(first_rec.get('summary', ''))} chars")
                    
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
                    print(f"   Response preview: {response.text[:200]}")
                    
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timed out (>60s)")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Wait between tests
        if i < len(test_conversations):
            print(f"   Waiting 3 seconds before next test...")
            time.sleep(3)
    
    # Test meal plan generation for comparison
    print(f"\n3️⃣ Testing Meal Plan Generation...")
    user_data = data.get("user", {})
    user_id = user_data.get("id")
    
    if user_id:
        start_time = time.time()
        try:
            response = session.post(f"{base_url}/api/meal-plans/text-input", json={
                "user_id": user_id,
                "input_text": "Create a simple 2 day healthy meal plan"
            }, timeout=120)  # Even longer timeout for meal plans
            
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            
            print(f"   Status: {response.status_code}")
            print(f"   Duration: {duration:.0f}ms ({duration/1000:.1f}s)")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"   ✅ Meal plan generated")
                print(f"   Meal plan ID: {response_data.get('id', 'N/A')}")
                
                # Check if response looks like real AI generation
                if duration > 5000:  # > 5 seconds indicates likely real AI
                    print(f"   ✅ Generation time reasonable for AI processing")
                else:
                    print(f"   ⚠️ Generation time suspiciously fast for AI")
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timed out (>120s)")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print(f"   ❌ No user ID available for meal plan test")
    
    print(f"\n" + "="*60)
    print("🎯 ANALYSIS SUMMARY")
    print("="*60)
    print("✅ If AI processing times are > 3-5 seconds with query analysis, likely working")
    print("⚠️ If response times are < 1 second or no query analysis, likely failing fast")
    print("❌ Check logs if responses seem suspicious")
    
if __name__ == "__main__":
    test_ai_recommendation_validity()