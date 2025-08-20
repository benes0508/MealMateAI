#!/usr/bin/env python3
"""
Clean API Test Script for Recipe Service
Tests all main endpoints with the populated vector database
"""

import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing Health Endpoint...")
    response = requests.get(f"{API_BASE}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Service: {data.get('service', 'unknown')}")
        print(f"   ✅ Status: {data.get('status', 'unknown')}")
        return True
    else:
        print(f"   ❌ Health check failed: {response.status_code}")
        return False

def test_collections():
    """Test collections endpoint"""
    print("\n📁 Testing Collections Endpoint...")
    response = requests.get(f"{API_BASE}/collections")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Total Collections: {data['total_collections']}")
        print(f"   ✅ Total Recipes: {data['total_recipes']}")
        print(f"   📊 Collections:")
        for col in data['collections'][:4]:
            print(f"      - {col['name']}: {col['recipe_count']} recipes")
        return True
    else:
        print(f"   ❌ Collections failed: {response.status_code}")
        return False

def test_search():
    """Test search endpoint"""
    print("\n🔍 Testing Search Endpoint...")
    
    test_queries = [
        {"query": "chocolate cake", "max_results": 3},
        {"query": "healthy salad", "max_results": 2},
        {"query": "pasta", "max_results": 2, "collections": ["comfort-cooked"]}
    ]
    
    for i, query_data in enumerate(test_queries, 1):
        print(f"\n   Test {i}: {query_data['query']}")
        response = requests.post(
            f"{API_BASE}/search",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            results_count = len(data['results'])
            processing_time = data.get('processing_time_ms', 0)
            
            print(f"      ✅ Found {results_count} results in {processing_time}ms")
            
            if results_count > 0:
                # Show top result
                top_result = data['results'][0]
                print(f"      🏆 Top: {top_result['title']} ({top_result['similarity_score']:.3f})")
                print(f"      📂 Collection: {top_result['collection']}")
            else:
                print(f"      ⚠️  No results found")
        else:
            print(f"      ❌ Search failed: {response.status_code}")
            return False
    
    return True

def test_collection_search():
    """Test collection-specific search"""
    print("\n🎯 Testing Collection-Specific Search...")
    
    response = requests.post(
        f"{API_BASE}/collections/desserts-sweets/search",
        json={"query": "chocolate dessert", "max_results": 2},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        results_count = len(data['results'])
        print(f"   ✅ Desserts search: {results_count} results")
        
        if results_count > 0:
            for i, result in enumerate(data['results'], 1):
                print(f"      {i}. {result['title']} ({result['similarity_score']:.3f})")
        return True
    else:
        print(f"   ❌ Collection search failed: {response.status_code}")
        return False

def test_recommendations():
    """Test AI recommendations endpoint"""
    print("\n🤖 Testing AI Recommendations...")
    
    conversation = [
        {"role": "user", "content": "I want something sweet for dessert tonight"},
        {"role": "assistant", "content": "What type of dessert are you in the mood for?"},
        {"role": "user", "content": "Something with chocolate would be perfect"}
    ]
    
    response = requests.post(
        f"{API_BASE}/recommendations",
        json={
            "conversation_history": conversation,
            "max_results": 3
        },
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        recommendations_count = len(data['recommendations'])
        processing_time = data.get('query_analysis', {}).get('processing_time_ms', 0)
        
        print(f"   ✅ AI generated {recommendations_count} recommendations in {processing_time}ms")
        
        # Show query analysis
        analysis = data.get('query_analysis', {})
        if analysis.get('detected_preferences'):
            print(f"   🧠 Detected preferences: {analysis['detected_preferences']}")
        
        # Show recommendations
        if recommendations_count > 0:
            print(f"   📋 Recommendations:")
            for i, rec in enumerate(data['recommendations'][:2], 1):
                print(f"      {i}. {rec['title']} ({rec['similarity_score']:.3f})")
        
        return True
    else:
        print(f"   ❌ Recommendations failed: {response.status_code}")
        if response.status_code == 500:
            try:
                error_data = response.json()
                print(f"      Error: {error_data.get('detail', 'Unknown error')}")
            except:
                pass
        return False

def main():
    """Run all API tests"""
    print("🧪 RECIPE SERVICE API TESTS")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Collections", test_collections), 
        ("Search", test_search),
        ("Collection Search", test_collection_search),
        ("AI Recommendations", test_recommendations)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    total_time = time.time() - start_time
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n" + "=" * 50)
    print(f"📊 TEST SUMMARY")
    print(f"   Passed: {passed}/{total}")
    print(f"   Time: {total_time:.1f}s")
    print()
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 All tests passed! Recipe Service is working perfectly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the details above.")

if __name__ == "__main__":
    main()