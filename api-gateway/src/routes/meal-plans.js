// src/routes/meal-plans.js

const express = require('express');
const {authenticateToken, isSameUser} = require('../middleware/auth');
const {createServiceProxy} = require('../utils/proxy');
const {createChatRateLimiter} = require('../middleware/rateLimiting');

const router = express.Router();

// Create a proxy to the meal planner service
const mealPlannerServiceProxy = createServiceProxy('meal-plans');

// Create chat rate limiter for AI-powered endpoints
const chatRateLimiter = createChatRateLimiter();

// All meal plan routes require authentication
router.use(authenticateToken);

// Get all user meal plans
router.get('/user/:userId', isSameUser, mealPlannerServiceProxy);

// Get the current meal plan for the authenticated user
router.get('/current', mealPlannerServiceProxy);

// Create a new meal plan
router.post('/', mealPlannerServiceProxy);

// AI-powered meal plan endpoints - apply chat rate limiting
// Generate a meal plan based on preferences
router.post('/generate', chatRateLimiter, mealPlannerServiceProxy);

// RAG-based meal plan endpoints (must come before /:id routes)
router.post('/rag/generate', chatRateLimiter, mealPlannerServiceProxy);
router.post('/rag/modify', chatRateLimiter, mealPlannerServiceProxy);
router.post('/rag/finalize', chatRateLimiter, mealPlannerServiceProxy);

// Text input meal plan generation (must come before /:id routes)
router.post('/text-input', chatRateLimiter, mealPlannerServiceProxy);

// Edit meal plan with text (must come before /:id routes)
router.post('/:id/edit-with-text', chatRateLimiter, mealPlannerServiceProxy);

// Get a specific meal plan
router.get('/:id', mealPlannerServiceProxy);

// Update a meal plan
router.put('/:id', mealPlannerServiceProxy);

// Delete a meal plan
router.delete('/:id', mealPlannerServiceProxy);

// Get grocery list for a meal plan
router.get('/:id/grocery-list', mealPlannerServiceProxy);

// Add a meal to a plan
router.post('/:id/meals', mealPlannerServiceProxy);

// Remove a meal from a plan
router.delete('/:id/meals/:mealId', mealPlannerServiceProxy);

// Update a meal in a plan
router.put('/:id/meals/:mealId', mealPlannerServiceProxy);

// Move a meal to a different day or meal type
router.post('/:id/move-meal', mealPlannerServiceProxy);

// Swap two days in a meal plan
router.post('/:id/swap-days', mealPlannerServiceProxy);

// Reorder days in a meal plan
router.post('/:id/reorder-days', mealPlannerServiceProxy);

// Replace a recipe in a meal plan
router.post('/:id/replace-recipe', mealPlannerServiceProxy);

module.exports = router;