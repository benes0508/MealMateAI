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
            print(f"  - User ID: {user.get('id')}, Username: {user.get('username')}, Email: {user.get('email')}, Name: {user.get('name')}")
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
        print(f"🔍 Retrieved user: ID: {user.get('id')}, Username: {user.get('username')}, Email: {user.get('email')}, Name: {user.get('name')}")
        return user
    else:
        print(f"❌ Failed to retrieve user with ID {user_id}. Status code: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def main():
    print("🚀 MealMate User Service Test Script")
    print_separator()
    
    # Wait a bit for the services to be fully up
    print("Waiting for services to be ready...")
    time.sleep(2)
    
    # First, check if we can get users (should be empty initially)
    print("Checking initial users in the database:")
    get_all_users()
    print_separator()
    
    # Create some test users
    print("Creating test users:")
    
    test_users = [
        {
            "username": "johndoe",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password": "securePassword123",
            "preferences": {
                "dietary_restrictions": ["vegetarian"],
                "allergies": ["nuts"],
                "favorite_cuisines": ["italian", "mexican"]
            }
        },
        {
            "username": "janesmith",
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "password": "janePwd456",
            "preferences": {
                "dietary_restrictions": ["vegan"],
                "allergies": ["gluten"],
                "favorite_cuisines": ["indian", "thai"]
            }
        },
        {
            "username": "alexj",
            "name": "Alex Johnson",
            "email": "alex@example.com",
            "password": "alexPass789",
            "preferences": {
                "dietary_restrictions": [],
                "allergies": ["dairy"],
                "favorite_cuisines": ["french", "japanese"]
            }
        }
    ]
    
    created_users = []
    for user_data in test_users:
        user = create_user(user_data)
        if user:
            created_users.append(user)
        # Small delay between requests
        time.sleep(0.5)
    
    print_separator()
    
    # Get all users to see the database has been populated
    print("Retrieving all users after creation:")
    get_all_users()
    print_separator()
    
    # Get specific users by ID
    if created_users:
        print("Retrieving specific user details:")
        get_user_by_id(created_users[0].get("id"))
    
    print_separator()
    print("✨ Test script completed!")

if __name__ == "__main__":
    main()