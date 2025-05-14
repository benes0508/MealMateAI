#!/usr/bin/env python3
"""
End-to-end test script for MealMateAI system

This script tests the complete flow of the MealMateAI system:
1. User registration and login
2. User preference setup
3. Recipe service integration
4. Meal plan creation with different parameters
5. Meal plan retrieval
6. Grocery list generation
7. Natural language meal plan generation

Usage:
    python test_end_to_end.py

Requirements:
    - All MealMateAI services should be running (via docker-compose)
    - Python 3.8+
    - Required packages: requests, pytest, python-dotenv
"""

import os
import sys
import json
import time
import random
import logging
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("MealMateAI-E2E-Test")

# Service base URLs - modify if ports or hosts differ in your environment
BASE_URLS = {
    "user": "http://localhost:8000",
    "recipe": "http://localhost:8001",
    "meal_planner": "http://localhost:8002",
    # "notification": "http://localhost:8003",
    # "api_gateway": "http://localhost:4000",
}

# Test user data
TEST_USER = {
    "email": f"test_user_{int(time.time())}@example.com",
    "username": f"test_user_{int(time.time())}",
    "password": "securePassword123!",
    "preferences": {
        "dietary_restrictions": ["vegetarian"],
        "allergies": ["peanuts", "shellfish"],
        "cuisine_preferences": ["italian", "mexican", "japanese"],
        "disliked_ingredients": ["cilantro", "olives"]
    }
}

class EndToEndTester:
    """Class to handle end-to-end testing of MealMateAI system"""
    
    def __init__(self):
        self.token = None
        self.user_id = None
        self.meal_plan_ids = []
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        try:
            self.check_services_health()
            self.register_user()
            self.login_user()
            self.update_user_preferences()
            
            # Test basic meal plan creation
            meal_plan_id = self.create_meal_plan(days=3, meals_per_day=3)
            self.meal_plan_ids.append(meal_plan_id)
            
            # Test meal plan with snacks
            meal_plan_id = self.create_meal_plan(days=2, meals_per_day=3, include_snacks=True)
            self.meal_plan_ids.append(meal_plan_id)
            
            # Test meal plan with additional preferences
            meal_plan_id = self.create_meal_plan(
                days=1, 
                meals_per_day=3,
                additional_preferences="High protein meals for workout days"
            )
            self.meal_plan_ids.append(meal_plan_id)
            
            # Test retrieving meal plans for user
            self.get_user_meal_plans()
            
            # Test retrieving a specific meal plan
            self.get_specific_meal_plan(self.meal_plan_ids[0])
            
            # Test generating grocery list
            self.generate_grocery_list(self.meal_plan_ids[0])
            
            # Test natural language meal plan generation
            self.create_meal_plan_from_text(
                "I need a 2-day meal plan with healthy breakfast and lunch options that are quick to prepare"
            )
            
            # Cleanup - delete created meal plans
            for plan_id in self.meal_plan_ids:
                self.delete_meal_plan(plan_id)
            
            logger.info("✅ All tests completed successfully!")
            return True
        
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            return False
    
    def check_services_health(self):
        """Check that all services are up and running"""
        logger.info("Checking services health...")
        
        for service_name, base_url in BASE_URLS.items():
            try:
                # Try the standard /health endpoint first
                health_url = f"{base_url}/health"
                response = requests.get(health_url, timeout=5)
                
                # If standard health endpoint fails, try alternative endpoints based on service
                if response.status_code != 200:
                    if service_name == "user":
                        # For user service, we can also check if /api/users endpoint is working
                        alt_url = f"{base_url}/api/users"
                        response = requests.get(alt_url, timeout=5)
                    elif service_name == "recipe":
                        # Alternative check for recipe service
                        alt_url = f"{base_url}/recipes"
                        response = requests.get(alt_url, timeout=5)
                    elif service_name == "api_gateway":
                        # API Gateway might have a different health check endpoint
                        alt_url = f"{base_url}/status"
                        response = requests.get(alt_url, timeout=5)
                
                if response.status_code == 200:
                    logger.info(f"✅ {service_name} service is healthy")
                else:
                    logger.warning(f"⚠️ {service_name} service returned status {response.status_code}, but continuing test")
            except requests.RequestException as e:
                logger.error(f"❌ Failed to connect to {service_name} service: {str(e)}")
                raise Exception(f"Failed to connect to {service_name} service")
    
    def register_user(self):
        """Register a new test user"""
        logger.info(f"Registering test user: {TEST_USER['username']}...")
        
        try:
            # Prepare user data according to the expected schema
            user_data = {
                "email": TEST_USER["email"],
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "full_name": f"Test User {int(time.time())}"  # Adding a full name
            }
            
            # Use the correct endpoint: /api/users/ instead of /users/register
            response = requests.post(
                f"{BASE_URLS['user']}/api/users/",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 201:
                user_data = response.json()
                self.user_id = user_data["id"]
                logger.info(f"✅ User registered successfully with ID: {self.user_id}")
            else:
                logger.error(f"❌ Failed to register user: {response.text}")
                raise Exception(f"Failed to register user: {response.text}")
        
        except requests.RequestException as e:
            logger.error(f"❌ Request failed during user registration: {str(e)}")
            raise Exception(f"Request failed during user registration: {str(e)}")
    
    def login_user(self):
        """Login as the test user"""
        logger.info(f"Logging in as user: {TEST_USER['username']}...")
        
        try:
            # For login, FastAPI expects form data not JSON
            login_data = {
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
            
            # Use the correct endpoint
            response = requests.post(
                f"{BASE_URLS['user']}/api/users/login",
                data=login_data,  # Using data instead of json for form data
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                # The actual response might be different based on your user_controller implementation
                # Adjust this based on the actual response format
                self.token = token_data.get("access_token") or token_data.get("message")
                logger.info("✅ Login successful")
            else:
                logger.error(f"❌ Failed to login: {response.text}")
                raise Exception(f"Failed to login: {response.text}")
        
        except requests.RequestException as e:
            logger.error(f"❌ Request failed during login: {str(e)}")
            raise Exception(f"Request failed during login: {str(e)}")
    
    def update_user_preferences(self):
        """Update user preferences"""
        logger.info("Updating user preferences...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Create update body according to the expected schema (UserUpdate)
            update_data = {
                "preferences": TEST_USER["preferences"]
            }
            
            # Use the correct endpoint - user_controller expects PUT to /api/users/{user_id}
            response = requests.put(
                f"{BASE_URLS['user']}/api/users/{self.user_id}",
                json=update_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ User preferences updated successfully")
            else:
                logger.error(f"❌ Failed to update preferences: {response.text}")
                raise Exception(f"Failed to update preferences: {response.text}")
        
        except requests.RequestException as e:
            logger.error(f"❌ Request failed during preferences update: {str(e)}")
            raise Exception(f"Request failed during preferences update: {str(e)}")
    
    def create_meal_plan(self, days=7, meals_per_day=3, include_snacks=False, additional_preferences=None):
        """Create a meal plan with the given parameters"""
        description = f"Creating meal plan for {days} days with {meals_per_day} meals per day"
        if include_snacks:
            description += " including snacks"
        if additional_preferences:
            description += f" and preferences: {additional_preferences}"
            
        logger.info(description)
        
        try:
            meal_plan_data = {
                "user_id": self.user_id,
                "days": days,
                "meals_per_day": meals_per_day,
                "include_snacks": include_snacks
            }
            
            if additional_preferences:
                meal_plan_data["additional_preferences"] = additional_preferences
            
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.post(
                f"{BASE_URLS['meal_planner']}/meal-plans/",
                json=meal_plan_data,
                headers=headers,
                timeout=30  # Longer timeout for meal plan generation
            )
            
            if response.status_code == 200:
                meal_plan = response.json()
                logger.info(f"✅ Meal plan created successfully with ID: {meal_plan['id']}")
                
                # Validate meal plan structure
                assert meal_plan["id"] > 0, "Meal plan ID should be positive"
                assert meal_plan["user_id"] == self.user_id, "User ID mismatch"
                assert len(meal_plan["recipes"]) > 0, "Meal plan should have recipes"
                
                return meal_plan["id"]
            else:
                logger.error(f"❌ Failed to create meal plan: {response.text}")
                raise Exception(f"Failed to create meal plan: {response.text}")
        
        except requests.RequestException as e:
            logger.error(f"❌ Request failed during meal plan creation: {str(e)}")
            raise Exception(f"Request failed during meal plan creation: {str(e)}")
    
    def get_user_meal_plans(self):
        """Retrieve all meal plans for the test user"""
        logger.info(f"Retrieving all meal plans for user: {self.user_id}...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(
                f"{BASE_URLS['meal_planner']}/meal-plans/user/{self.user_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                meal_plans = response.json()
                logger.info(f"✅ Retrieved {len(meal_plans)} meal plans")
                
                # Validate we have the expected number of meal plans
                assert len(meal_plans) >= len(self.meal_plan_ids), f"Expected at least {len(self.meal_plan_ids)} meal plans"
                
                return meal_plans
            else:
                logger.error(f"❌ Failed to retrieve meal plans: {response.text}")
                raise Exception(f"Failed to retrieve meal plans: {response.text}")
        
        except requests.RequestException as e:
            logger.error(f"❌ Request failed during meal plan retrieval: {str(e)}")
            raise Exception(f"Request failed during meal plan retrieval: {str(e)}")
    
    def get_specific_meal_plan(self, meal_plan_id):
        """Retrieve a specific meal plan by ID"""
        logger.info(f"Retrieving meal plan with ID: {meal_plan_id}...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(
                f"{BASE_URLS['meal_planner']}/meal-plans/{meal_plan_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                meal_plan = response.json()
                logger.info(f"✅ Retrieved meal plan: {meal_plan['plan_name']}")
                return meal_plan
            else:
                logger.error(f"❌ Failed to retrieve meal plan: {response.text}")
                raise Exception(f"Failed to retrieve meal plan: {response.text}")
        
        except requests.RequestException as e:
            logger.error(f"❌ Request failed during specific meal plan retrieval: {str(e)}")
            raise Exception(f"Request failed during specific meal plan retrieval: {str(e)}")
    
    def generate_grocery_list(self, meal_plan_id):
        """Generate a grocery list for a specific meal plan"""
        logger.info(f"Generating grocery list for meal plan ID: {meal_plan_id}...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(
                f"{BASE_URLS['meal_planner']}/meal-plans/{meal_plan_id}/grocery-list",
                headers=headers,
                timeout=20
            )
            
            if response.status_code == 200:
                grocery_list = response.json()
                logger.info(f"✅ Generated grocery list with {len(grocery_list['items'])} items")
                
                # Validate grocery list structure
                assert "items" in grocery_list, "Grocery list should have items"
                assert len(grocery_list["items"]) > 0, "Grocery list should not be empty"
                
                return grocery_list
            else:
                logger.error(f"❌ Failed to generate grocery list: {response.text}")
                raise Exception(f"Failed to generate grocery list: {response.text}")
        
        except requests.RequestException as e:
            logger.error(f"❌ Request failed during grocery list generation: {str(e)}")
            raise Exception(f"Request failed during grocery list generation: {str(e)}")
    
    def create_meal_plan_from_text(self, input_text):
        """Create a meal plan using natural language input"""
        logger.info(f"Creating meal plan from text: '{input_text}'...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            data = {
                "input_text": input_text
            }
            
            response = requests.post(
                f"{BASE_URLS['meal_planner']}/meal-plans/text-input?user_id={self.user_id}",
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                meal_plan = response.json()
                logger.info(f"✅ Created meal plan from text: {meal_plan['plan_name']}")
                
                # Store the meal plan ID for cleanup
                self.meal_plan_ids.append(meal_plan["id"])
                
                return meal_plan
            else:
                logger.error(f"❌ Failed to create meal plan from text: {response.text}")
                raise Exception(f"Failed to create meal plan from text: {response.text}")
        
        except requests.RequestException as e:
            logger.error(f"❌ Request failed during text-based meal plan creation: {str(e)}")
            raise Exception(f"Request failed during text-based meal plan creation: {str(e)}")
    
    def delete_meal_plan(self, meal_plan_id):
        """Delete a meal plan by ID"""
        logger.info(f"Deleting meal plan with ID: {meal_plan_id}...")
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.delete(
                f"{BASE_URLS['meal_planner']}/meal-plans/{meal_plan_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Deleted meal plan with ID: {meal_plan_id}")
                return True
            else:
                logger.error(f"❌ Failed to delete meal plan: {response.text}")
                return False
        
        except requests.RequestException as e:
            logger.error(f"❌ Request failed during meal plan deletion: {str(e)}")
            return False


def main():
    """Main function to run the end-to-end test"""
    parser = argparse.ArgumentParser(description='Run end-to-end tests for MealMateAI')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("Starting MealMateAI end-to-end tests")
    logger.info(f"Test timestamp: {datetime.now().isoformat()}")
    
    tester = EndToEndTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()