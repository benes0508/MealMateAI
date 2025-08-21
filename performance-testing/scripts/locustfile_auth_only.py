"""
MealMateAI Authentication & User Management Performance Test
Tests authentication flows and user-related CRUD operations.
SAFE - No AI API calls, no cost implications.
"""

from locust import HttpUser, task, between, events
import random
import json
import uuid
import time
from faker import Faker

# Initialize Faker for realistic test data
fake = Faker()

# Track metrics
auth_success_count = 0
auth_failure_count = 0
registration_count = 0

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary statistics when test stops"""
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    Test Summary                              ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Registrations: {registration_count:>10}                              ║
    ║  Successful Logins: {auth_success_count:>6}                              ║
    ║  Failed Logins: {auth_failure_count:>10}                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

class AuthenticationUser(HttpUser):
    """
    Simulates user authentication and profile management workflows.
    Tests registration, login, profile updates, and preference management.
    """
    
    wait_time = between(1, 2)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registered_users = []  # Track users for login testing
    
    def on_start(self):
        """Initialize test user data"""
        self.test_user_base = f"perf_{uuid.uuid4().hex[:6]}"
        self.current_user = None
        self.auth_token = None
        
        # Pre-register some users for login testing
        for i in range(3):
            self.register_test_user()
    
    def register_test_user(self):
        """Helper to register a test user"""
        global registration_count
        
        user_data = {
            "email": f"{self.test_user_base}_{len(self.registered_users)}@test.local",
            "password": "SecurePass123!",
            "name": fake.name(),
            "phone": fake.phone_number()[:15],  # Limit length
        }
        
        with self.client.post("/api/auth/register",
                             json=user_data,
                             name="Register New User",
                             catch_response=True) as response:
            if response.status_code in [200, 201]:
                registration_count += 1
                self.registered_users.append(user_data)
                response.success()
                return user_data
            elif response.status_code == 409:
                # User already exists
                response.success()
                return user_data
            else:
                response.failure(f"Registration failed: {response.status_code}")
                return None
    
    @task(10)
    def login_logout_cycle(self):
        """Test login and logout flow"""
        global auth_success_count, auth_failure_count
        
        if not self.registered_users:
            self.register_test_user()
            return
        
        # Pick a random registered user
        user = random.choice(self.registered_users)
        
        # Login
        with self.client.post("/api/auth/login",
                             json={
                                 "email": user["email"],
                                 "password": user["password"]
                             },
                             name="User Login",
                             catch_response=True) as response:
            if response.status_code == 200:
                auth_success_count += 1
                data = response.json()
                self.auth_token = data.get("access_token", data.get("token"))
                self.current_user = data.get("user", {})
                
                # Update headers for authenticated requests
                self.client.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                # Simulate some authenticated activity
                time.sleep(random.uniform(0.5, 2))
                
                # Logout (if endpoint exists)
                self.logout_user()
            else:
                auth_failure_count += 1
                response.failure(f"Login failed: {response.status_code}")
    
    @task(5)
    def failed_login_attempt(self):
        """Test login with invalid credentials"""
        global auth_failure_count
        
        with self.client.post("/api/auth/login",
                             json={
                                 "email": f"invalid_{uuid.uuid4().hex}@test.local",
                                 "password": "WrongPassword"
                             },
                             name="Failed Login Attempt",
                             catch_response=True) as response:
            if response.status_code in [401, 403]:
                # Expected failure
                auth_failure_count += 1
                response.success()
            elif response.status_code == 200:
                response.failure("Login succeeded with invalid credentials!")
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(3)
    def register_new_user(self):
        """Register a new user during the test"""
        self.register_test_user()
    
    @task(8)
    def get_current_user_profile(self):
        """Get current user information"""
        if not self.auth_token:
            self.login_logout_cycle()
            return
        
        with self.client.get("/api/users/me",
                            name="Get Current User",
                            catch_response=True) as response:
            if response.status_code == 200:
                self.current_user = response.json()
            elif response.status_code == 401:
                # Token expired, re-login
                self.auth_token = None
                response.success()
            else:
                response.failure(f"Failed to get user: {response.status_code}")
    
    @task(6)
    def update_user_profile(self):
        """Update user profile information"""
        if not self.auth_token or not self.current_user:
            self.login_logout_cycle()
            return
        
        user_id = self.current_user.get("id")
        if not user_id:
            return
        
        updated_data = {
            "name": fake.name(),
            "phone": fake.phone_number()[:15],
            "bio": fake.text(max_nb_chars=200),
            "location": fake.city()
        }
        
        with self.client.put(f"/api/users/{user_id}",
                            json=updated_data,
                            name="Update User Profile",
                            catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 401:
                self.auth_token = None
                response.success()
            else:
                response.failure(f"Update failed: {response.status_code}")
    
    @task(7)
    def manage_user_preferences(self):
        """Get and update user preferences"""
        if not self.auth_token or not self.current_user:
            self.login_logout_cycle()
            return
        
        user_id = self.current_user.get("id")
        if not user_id:
            return
        
        # Get current preferences
        with self.client.get(f"/api/users/{user_id}/preferences",
                            name="Get Preferences",
                            catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            elif response.status_code == 401:
                self.auth_token = None
                response.success()
                return
            else:
                response.failure(f"Failed to get preferences: {response.status_code}")
        
        # Update preferences
        preferences = {
            "dietary_restrictions": random.choice([
                [],
                ["vegetarian"],
                ["vegan"],
                ["gluten-free"],
                ["dairy-free"],
                ["vegetarian", "gluten-free"]
            ]),
            "allergies": random.choice([
                [],
                ["peanuts"],
                ["tree nuts"],
                ["dairy"],
                ["eggs"],
                ["shellfish"],
                ["soy"]
            ]),
            "cuisine_preferences": random.sample(
                ["italian", "mexican", "chinese", "indian", "thai", "japanese", "french", "greek"],
                k=random.randint(1, 3)
            ),
            "cooking_skill": random.choice(["beginner", "intermediate", "advanced", "expert"]),
            "kitchen_equipment": random.sample(
                ["oven", "stove", "microwave", "slow cooker", "instant pot", "air fryer", "grill"],
                k=random.randint(2, 4)
            ),
            "meal_prep_time": random.choice([15, 30, 45, 60, 90, 120]),
            "servings": random.choice([1, 2, 4, 6]),
            "budget": random.choice(["low", "medium", "high"]),
            "health_goals": random.choice([None, "weight loss", "muscle gain", "maintenance", "heart health"])
        }
        
        with self.client.put(f"/api/users/{user_id}/preferences",
                            json=preferences,
                            name="Update Preferences",
                            catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 401:
                self.auth_token = None
                response.success()
            else:
                response.failure(f"Preference update failed: {response.status_code}")
    
    @task(2)
    def password_reset_flow(self):
        """Test password reset request (not actual reset)"""
        if not self.registered_users:
            return
        
        user = random.choice(self.registered_users)
        
        # Request password reset
        with self.client.post("/api/auth/forgot-password",
                             json={"email": user["email"]},
                             name="Password Reset Request",
                             catch_response=True) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            elif response.status_code == 404:
                # Endpoint might not exist
                response.success()
            else:
                response.failure(f"Reset request failed: {response.status_code}")
    
    @task(1)
    def validate_token(self):
        """Validate JWT token"""
        if not self.auth_token:
            return
        
        with self.client.get("/api/auth/validate",
                            name="Validate Token",
                            catch_response=True) as response:
            if response.status_code in [200, 401, 404]:
                response.success()
            else:
                response.failure(f"Validation failed: {response.status_code}")
    
    @task(4)
    def concurrent_login_test(self):
        """Test multiple login attempts for same user"""
        if not self.registered_users:
            self.register_test_user()
            return
        
        user = self.registered_users[0]  # Use first user
        
        # Attempt multiple logins rapidly
        for i in range(3):
            with self.client.post("/api/auth/login",
                                 json={
                                     "email": user["email"],
                                     "password": user["password"]
                                 },
                                 name="Concurrent Login",
                                 catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 429:
                    # Rate limited - expected
                    response.success()
                    break
                else:
                    response.failure(f"Concurrent login failed: {response.status_code}")
            
            time.sleep(0.1)  # Small delay between attempts
    
    def logout_user(self):
        """Logout current user"""
        if not self.auth_token:
            return
        
        with self.client.post("/api/auth/logout",
                             name="User Logout",
                             catch_response=True) as response:
            if response.status_code in [200, 204, 404]:
                # Logout successful or endpoint doesn't exist
                self.auth_token = None
                self.current_user = None
                self.client.headers.pop("Authorization", None)
                response.success()
            else:
                response.failure(f"Logout failed: {response.status_code}")
    
    def on_stop(self):
        """Cleanup when test stops"""
        if self.auth_token:
            self.logout_user()
        print(f"🏁 Test user {self.test_user_base} completed")


class AdminAuthenticationUser(HttpUser):
    """
    Test admin authentication and authorization.
    Separate class to avoid mixing with regular user flows.
    """
    
    wait_time = between(3, 5)
    weight = 1  # Lower weight since admins are fewer
    
    @task
    def admin_login_attempt(self):
        """Attempt admin login"""
        # Use predefined admin credentials (should exist in test env)
        with self.client.post("/api/auth/login",
                             json={
                                 "email": "admin@mealmate.local",
                                 "password": "AdminPass123!"
                             },
                             name="Admin Login",
                             catch_response=True) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Admin login unexpected: {response.status_code}")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║      MealMateAI Authentication Performance Test              ║
    ║                                                              ║
    ║  ✅ SAFE: No AI API calls                                   ║
    ║  ✅ SAFE: Authentication and user management only           ║
    ║                                                              ║
    ║  Test Scenarios:                                            ║
    ║  - User registration with validation                        ║
    ║  - Login/logout cycles                                      ║
    ║  - Failed login attempts                                    ║
    ║  - JWT token validation                                     ║
    ║  - User profile CRUD operations                             ║
    ║  - Preference management                                    ║
    ║  - Concurrent login testing                                 ║
    ║  - Password reset flows                                     ║
    ║  - Admin authentication                                     ║
    ║                                                              ║
    ║  Run with: locust -f locustfile_auth_only.py                ║
    ╚══════════════════════════════════════════════════════════════╝
    """)