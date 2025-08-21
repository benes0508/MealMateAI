// src/index.js
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const winston = require('winston');
const expressWinston = require('express-winston');
const config = require('./config/config');

// Import route handlers
const usersRoutes = require('./routes/users');
const recipesRoutes = require('./routes/recipes');
const mealPlansRoutes = require('./routes/meal-plans');
const notificationsRoutes = require('./routes/notifications');

const app = express();

// Trust proxy - important when running behind Nginx
app.set('trust proxy', 1);

// Apply security middleware
app.use(helmet());

// Configure CORS to allow requests from the frontend container
app.use(cors({
  origin: ['http://localhost', 'http://frontend', 'http://localhost:80'],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Rate limiting with bypass for testing - DISABLED FOR TESTING
if (!config.BYPASS_RATE_LIMIT_FOR_TESTS) {
  const limiter = rateLimit({
    windowMs: config.RATE_LIMIT_WINDOW_MS,
    max: config.RATE_LIMIT_MAX,
    standardHeaders: true,
    legacyHeaders: false,
    skip: (req) => {
      // Skip rate limiting if bypass header is present
      if (req.headers['x-bypass-rate-limit'] === 'true') {
        return true;
      }
      return false;
    }
  });
  app.use(limiter);
} else {
  console.log('[API-GATEWAY] Global rate limiting DISABLED for testing');
}

// Request logging
app.use(morgan('combined'));
app.use(expressWinston.logger({
  transports: [
    new winston.transports.Console()
  ],
  format: winston.format.combine(
    winston.format.colorize(),
    winston.format.simple()
  ),
  meta: false,
  msg: "HTTP {{req.method}} {{req.url}}",
  expressFormat: true,
  colorize: true
}));

// Request parsing middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Simple health check
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', message: 'API Gateway is running' });
});

// Mount service routes
app.use('/api/users', usersRoutes);
app.use('/api/recipes', recipesRoutes);
app.use('/api/meal-plans', mealPlansRoutes);
app.use('/api/notifications', notificationsRoutes);

// Proxy image requests to Recipe Service
const { createProxyMiddleware } = require('http-proxy-middleware');
app.use('/images', createProxyMiddleware({
  target: config.RECIPE_SERVICE_URL,
  changeOrigin: true,
  logLevel: 'debug'
}));

// Error logging
app.use(expressWinston.errorLogger({
  transports: [
    new winston.transports.Console()
  ],
  format: winston.format.combine(
    winston.format.colorize(),
    winston.format.json()
  )
}));

// Catch-all for 404 errors
app.use((req, res) => {
  res.status(404).json({ message: 'Resource not found' });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error(err);
  res.status(err.status || 500).json({
    message: err.message || 'Something went wrong',
    error: process.env.NODE_ENV === 'production' ? {} : err
  });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`API Gateway running on port ${PORT}`);
});

module.exports = app; // For testing purposes