# User Service Tests

This directory contains tests for the User Service API.

## API Tests

### Running the API Tests

To run the API test script, ensure your services are running first:

```bash
# From the project root directory
docker-compose up
```

Then in a new terminal:

```bash
# From the user-service/tests directory
python test_user_api.py
```

You can also specify a custom API endpoint using an environment variable:

```bash
USER_SERVICE_URL=http://localhost:8000 python test_user_api.py
```

## What the Tests Do

The API tests perform the following actions:
1. Retrieve the initial list of users (to verify the database state)
2. Create test users with different preferences and dietary restrictions
3. Verify the users were created by retrieving them
4. Test retrieving specific user details

## Database Verification

After running the tests, you can verify the database contents directly:

```bash
# Connect to the MySQL container
docker exec -it mealmateai_mysql_1 mysql -uuser_service_user -puser_service_password user_service_db

# Once connected to MySQL, run:
SELECT * FROM users;
```