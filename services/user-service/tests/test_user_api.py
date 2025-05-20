#!/usr/bin/env python3
import requests
import json
import time
import os
import sys

# Add the parent directory to sys.path to allow imports from the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Base URL for the user service - configurable for local or containerized testing
BASE_URL = os.environ.get("USER_SERVICE_URL", "http://localhost:8000")

def print_separator():
    print("\n" + "="*50 + "\n")

def create_user(user_data):
    """Create a new user with the given data"""
    response = requests.post(f"{BASE_URL}/api/users/", json=user_data)
    if response.status_code == 201:
        print(f"✅ User created successfully: {response.json()}")
        return response.json()
    else:
        print(f"❌ Failed to create user. Status code: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def get_all_users():
    """Get all users from the service"""
    response = requests.get(f"{BASE_URL}/api/users/")
    if response.status_code == 200:
        users = response.json()
        print(f"📋 Retrieved {len(users)} users:")
        for user in users:
            print(f"  - User ID: {user.get('id')}, Username: {user.get('username')}, Email: {user.get('email')}, Name: {user.get('full_name')}")
        return users
    else:
        print(f"❌ Failed to retrieve users. Status code: {response.status_code}")
        print(f"Error: {response.text}")
        return []

def get_user_by_id(user_id):
    """Get a specific user by ID"""
    response = requests.get(f"{BASE_URL}/api/users/{user_id}")
    if response.status_code == 200:
        user = response.json()
        print(f"Found user: {user.get('username')}")
        return user
    else:
        print(f"❌ Failed to retrieve user with ID {user_id}. Status code: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def login_user(username, password):
    """Login with username and password"""
    response = requests.post(f"{BASE_URL}/api/users/login", params={"username": username, "password": password})
    if response.status_code == 200:
        print(f"✅ User login successful")
        return response.json()
    else:
        print(f"❌ Login failed. Status code: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def update_user_preferences(user_id, preferences_data):
    """Update a user's preferences"""
    response = requests.put(f"{BASE_URL}/api/users/{user_id}/preferences", json=preferences_data)
    if response.status_code == 200:
        print(f"✅ User preferences updated successfully")
        return response.json()
    else:
        print(f"❌ Failed to update preferences. Status code: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def main():
    print("🚀 MealMate User Service Test Script")
    print_separator()
    
    # Wait a bit for the services to be fully up
    print("Waiting for services to be ready...")
    time.sleep(2)
    
    # First, check if we can get users
    print("Checking initial users in the database:")
    get_all_users()
    print_separator()
    
    # Create a test user with basic info first
    print("Creating a basic test user:")
    timestamp = int(time.time())
    test_user = {
        "username": f"test_user_{timestamp}",
        "email": f"test_user_{timestamp}@example.com",
        "password": "TestPass123!",
        "full_name": f"Test User {timestamp}"
    }
    
    created_user = create_user(test_user)
    if not created_user:
        print("Failed to create test user, exiting")
        return
    
    print_separator()
    
    # Now create a user with preferences included
    print("Creating a test user with preferences:")
    timestamp = int(time.time())
    preference_user = {
        "username": f"foodie_{timestamp}",
        "email": f"foodie_{timestamp}@example.com", 
        "password": "FoodiePass456!",
        "full_name": f"Foodie User {timestamp}",
        "allergies": ["peanuts", "shellfish"],
        "disliked_ingredients": ["cilantro", "olives"],
        "preferred_cuisines": ["italian", "mexican", "japanese"],
        "preferences": {
            "dietary_restrictions": ["vegetarian"],
            "cooking_skill": "intermediate",
            "meal_prep_time": "30-60min"
        }
    }
    
    foodie_user = create_user(preference_user)
    if foodie_user:
        print("\nTest user with preferences created successfully!")
        
        # Get and verify user details
        user_details = get_user_by_id(foodie_user["id"])
        if user_details:
            print("\nVerifying preference fields:")
            print(f"- Allergies: {user_details.get('allergies', [])}")
            print(f"- Disliked ingredients: {user_details.get('disliked_ingredients', [])}")
            print(f"- Preferred cuisines: {user_details.get('preferred_cuisines', [])}")
            print(f"- Preferences: {json.dumps(user_details.get('preferences', {}), indent=2)}")
            
        # Test login
        print("\nTesting login with preference user:")
        login_user(preference_user["username"], preference_user["password"])
    
    print_separator()
    
    # Test updating preferences on existing user
    if created_user:
        print("Testing preference update on the basic user:")
        new_preferences = {
            "allergies": ["dairy", "gluten"],
            "disliked_ingredients": ["mushrooms", "eggplant"],
            "preferred_cuisines": ["greek", "thai", "vietnamese"],
            "preferences": {
                "dietary_restrictions": ["gluten-free", "dairy-free"],
                "cooking_skill": "beginner",
                "meal_prep_time": "15-30min"
            }
        }
        
        updated_user = update_user_preferences(created_user["id"], new_preferences)
        if updated_user:
            # Get and verify updated user details
            print("\nVerifying updated preference fields:")
            print(f"- Allergies: {updated_user.get('allergies', [])}")
            print(f"- Disliked ingredients: {updated_user.get('disliked_ingredients', [])}")
            print(f"- Preferred cuisines: {updated_user.get('preferred_cuisines', [])}")
            print(f"- Preferences: {json.dumps(updated_user.get('preferences', {}), indent=2)}")
    
    print_separator()
    print("Final user list after tests:")
    get_all_users()
    
    print_separator()
    print("✨ Test script completed!")

if __name__ == "__main__":
    main()