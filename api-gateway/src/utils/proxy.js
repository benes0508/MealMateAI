// src/utils/proxy.js

const { createProxyMiddleware } = require('http-proxy-middleware');
const { 
  USER_SERVICE_URL, 
  RECIPE_SERVICE_URL, 
  MEAL_PLANNER_SERVICE_URL,
  NOTIFICATION_SERVICE_URL
} = require('../config/config');

/**
 * Creates a proxy middleware for forwarding requests to microservices
 * @param {string} serviceName - The name of the service to route to
 * @returns {Function} - The proxy middleware function
 */
const createServiceProxy = (serviceName) => {
  let target;
  let pathRewrite = {};

  switch (serviceName) {
    case 'users':
      target = USER_SERVICE_URL;
      pathRewrite = { '^/api/users': '' }; // Rewrite /api/users to / for user service
      break;
    case 'recipes':
      target = RECIPE_SERVICE_URL;
      pathRewrite = { '^/api/recipes': '' }; // Rewrite /api/recipes to / for recipe service
      break;
    case 'meal-plans':
      target = MEAL_PLANNER_SERVICE_URL;
      pathRewrite = { '^/api/meal-plans': '' }; // Rewrite /api/meal-plans to / for meal planner service
      break;
    case 'notifications':
      target = NOTIFICATION_SERVICE_URL;
      pathRewrite = { '^/api/notifications': '' }; // Rewrite /api/notifications to / for notification service
      break;
    default:
      throw new Error(`Unknown service: ${serviceName}`);
  }

  return createProxyMiddleware({
    target,
    changeOrigin: true,
    pathRewrite,
    logLevel: 'silent', // Options: 'debug', 'info', 'warn', 'error', 'silent'
    onError: (err, req, res) => {
      console.error(`Proxy error for ${serviceName} service:`, err);
      res.status(500).json({
        message: `Service ${serviceName} is currently unavailable`,
        error: process.env.NODE_ENV === 'production' ? undefined : err.message
      });
    },
    onProxyReq: (proxyReq, req, res) => {
      // Add custom headers or modify the proxy request if needed
      if (req.user) {
        // Pass user ID to microservices for authorization
        proxyReq.setHeader('X-User-ID', req.user.id);
        proxyReq.setHeader('X-User-Role', req.user.role || 'user');
      }
      
      // Log request
      console.log(`Proxying ${req.method} ${req.path} to ${serviceName} service`);
    },
    onProxyRes: (proxyRes, req, res) => {
      // Modify the proxy response if needed
      // For example, add custom headers or log response metrics
    }
  });
};

module.exports = { createServiceProxy };