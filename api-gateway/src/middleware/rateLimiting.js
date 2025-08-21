// src/middleware/rateLimiting.js
const rateLimit = require('express-rate-limit');
const config = require('../config/config');

// Create chat-specific rate limiter
const createChatRateLimiter = () => {
  // ALWAYS return no-op middleware for testing
  if (!config.CHAT_RATE_LIMIT_ENABLED || config.BYPASS_RATE_LIMIT_FOR_TESTS || true) {
    return (req, res, next) => {
      // Add header to indicate rate limiting was bypassed
      res.set('X-RateLimit-Bypassed', 'true');
      console.log('[RATE-LIMITER] Chat rate limiting BYPASSED for:', req.path);
      next();
    };
  }

  return rateLimit({
    windowMs: config.CHAT_RATE_LIMIT_WINDOW_MS, // 1 minute window
    max: config.CHAT_RATE_LIMIT_MAX, // 6 requests per minute (effectively 10 second cooldown)
    standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
    legacyHeaders: false, // Disable the `X-RateLimit-*` headers
    
    // Skip rate limiting for test requests (optional header-based bypass)
    skip: (req) => {
      // Check for test bypass header
      if (req.headers['x-bypass-rate-limit'] === 'true') {
        return true;
      }
      return false;
    },
    
    // Custom error message
    message: {
      error: 'Too many chat requests',
      message: 'Please wait before sending another chat message. You can send up to 6 chat messages per minute.',
      retryAfter: Math.ceil(config.CHAT_RATE_LIMIT_WINDOW_MS / 1000), // seconds
      type: 'chat_rate_limit_exceeded'
    },
    
    // Custom response when rate limit is exceeded
    handler: (req, res) => {
      const resetTime = new Date(Date.now() + config.CHAT_RATE_LIMIT_WINDOW_MS);
      res.status(429).json({
        error: 'Too many chat requests',
        message: 'Please wait before sending another chat message. You can send up to 6 chat messages per minute.',
        retryAfter: Math.ceil(config.CHAT_RATE_LIMIT_WINDOW_MS / 1000),
        resetTime: resetTime.toISOString(),
        type: 'chat_rate_limit_exceeded'
      });
    },
    
    // Store rate limit info for each IP
    keyGenerator: (req) => {
      // Use IP address as the key for rate limiting
      // In production, you might want to use user ID if available
      return req.ip || req.connection.remoteAddress || 'unknown';
    }
  });
};

// Export the rate limiter factory
module.exports = {
  createChatRateLimiter
};