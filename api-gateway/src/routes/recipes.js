const express = require('express');
const { authenticateToken, isAdmin } = require('../middleware/auth');
const { createServiceProxy } = require('../utils/proxy');

const router = express.Router();

// Create a proxy to the recipe service
const recipeServiceProxy = createServiceProxy('recipes');

// Public routes for recipe browsing
router.get('/', recipeServiceProxy);
router.get('/search', recipeServiceProxy);
router.get('/tags', recipeServiceProxy);
router.get('/categories', recipeServiceProxy);
router.get('/csv', recipeServiceProxy); // New endpoint for CSV recipes
router.get('/collections', recipeServiceProxy); // Get all collections
router.get('/collections/:name/info', recipeServiceProxy); // Get collection info
router.post('/collections/:name/search', authenticateToken, recipeServiceProxy); // Collection search - requires auth for user context
router.post('/recommendations', authenticateToken, recipeServiceProxy); // AI recommendations - requires auth
router.post('/search', recipeServiceProxy); // Direct search - public
router.get('/:id', recipeServiceProxy); // This must be last as it's a catch-all

// Protected routes that require authentication
router.use(authenticateToken);

// Routes for user-specific recipe actions
router.post('/favorites/:id', recipeServiceProxy);
router.delete('/favorites/:id', recipeServiceProxy);
router.get('/favorites', recipeServiceProxy);
router.get('/recommendations', recipeServiceProxy);

// Admin-only routes
router.post('/', isAdmin, recipeServiceProxy);
router.put('/:id', isAdmin, recipeServiceProxy);
router.delete('/:id', isAdmin, recipeServiceProxy);

module.exports = router;