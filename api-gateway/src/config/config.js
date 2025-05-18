// Environment variables with defaults
const PORT = process.env.PORT || 4000;
const NODE_ENV = process.env.NODE_ENV || 'development';

// Service URLs
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://user-service:8000';
const RECIPE_SERVICE_URL = process.env.RECIPE_SERVICE_URL || 'http://recipe-service:8001';
const MEAL_PLANNER_SERVICE_URL = process.env.MEAL_PLANNER_SERVICE_URL || 'http://meal-planner-service:8002';
const NOTIFICATION_SERVICE_URL = process.env.NOTIFICATION_SERVICE_URL || 'http://notification-service:8003';

// JWT configuration
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-for-development-only';
const JWT_EXPIRY = process.env.JWT_EXPIRY || '1d';

// CORS configuration
const CORS_ORIGIN = process.env.CORS_ORIGIN || '*';

// Rate limiting
const RATE_LIMIT_WINDOW_MS = process.env.RATE_LIMIT_WINDOW_MS || 15 * 60 * 1000; // 15 minutes
const RATE_LIMIT_MAX = process.env.RATE_LIMIT_MAX || 100; // 100 requests per window

module.exports = {
  PORT,
  NODE_ENV,
  USER_SERVICE_URL,
  RECIPE_SERVICE_URL,
  MEAL_PLANNER_SERVICE_URL,
  NOTIFICATION_SERVICE_URL,
  JWT_SECRET,
  JWT_EXPIRY,
  CORS_ORIGIN,
  RATE_LIMIT_WINDOW_MS,
  RATE_LIMIT_MAX,
};