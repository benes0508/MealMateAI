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
      // No path rewrite for user service
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
    logLevel: 'debug',
    timeout: 30000,
    proxyTimeout: 30000,
    onError: (err, req, res) => {
      console.error(`[PROXY ERROR] ${serviceName} service error:`, err);
      console.error(`[PROXY ERROR] Request details: ${req.method} ${req.originalUrl} -> ${target}${req.path}`);
      console.error(`[PROXY ERROR] Headers:`, req.headers);
      
      res.status(502).json({
        message: `Service ${serviceName} is currently unavailable`,
        error: process.env.NODE_ENV === 'production' ? undefined : err.message
      });
    },
    onProxyReq: (proxyReq, req, res) => {
      // Log full request details
      console.log(`[PROXY REQUEST] --------------------------------------------------------`);
      console.log(`[PROXY REQUEST] ${req.method} ${req.originalUrl} -> ${target}${req.path}`);
      console.log(`[PROXY REQUEST] Headers:`, JSON.stringify(req.headers));
      
      // Log request body for debugging if it's a POST/PUT
      if (req.body && (req.method === 'POST' || req.method === 'PUT')) {
        const bodyData = JSON.stringify(req.body);
        console.log(`[PROXY REQUEST] Body: ${bodyData}`);
        
        // Need to rewrite body to the proxied request since we've already read it
        proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
        proxyReq.write(bodyData);
        proxyReq.end();
      }
      
      if (req.user) {
        proxyReq.setHeader('X-User-ID', req.user.id);
        proxyReq.setHeader('X-User-Role', req.user.role || 'user');
      }
      
      // Log the full target URL
      console.log(`[PROXY REQUEST] Full target URL: ${target}${req.path}`);
    },
    onProxyRes: (proxyRes, req, res) => {
      console.log(`[PROXY RESPONSE] --------------------------------------------------------`);
      console.log(`[PROXY RESPONSE] ${proxyRes.statusCode} ${proxyRes.statusMessage} for ${req.method} ${req.originalUrl}`);
      console.log(`[PROXY RESPONSE] Headers:`, JSON.stringify(proxyRes.headers));
      
      // Collect response body for logging
      let responseBody = '';
      proxyRes.on('data', (chunk) => {
        responseBody += chunk;
      });
      
      proxyRes.on('end', () => {
        try {
          // Try to parse as JSON for better logging
          const parsedBody = JSON.parse(responseBody);
          console.log(`[PROXY RESPONSE] Body: `, JSON.stringify(parsedBody));
        } catch (e) {
          // If not JSON or too large, log truncated
          if (responseBody.length > 300) {
            console.log(`[PROXY RESPONSE] Body (truncated): ${responseBody.substring(0, 300)}...`);
          } else {
            console.log(`[PROXY RESPONSE] Body: ${responseBody}`);
          }
        }
      });
    }
  });
};

module.exports = { createServiceProxy };