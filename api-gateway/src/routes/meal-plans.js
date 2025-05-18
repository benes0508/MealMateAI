// src/routes/meal-plans.js

const express = require('express');
const { authenticateToken, isSameUser } = require('../middleware/auth');
const { createServiceProxy } = require('../utils/proxy');

const router = express.Router();

// Create a proxy to the meal planner service
const mealPlannerServiceProxy = createServiceProxy('meal-plans');

// All meal plan routes require authentication
router.use(authenticateToken);

// Get all user meal plans
router.get('/user/:userId', isSameUser, mealPlannerServiceProxy);

// Create a new meal plan
router.post('/', mealPlannerServiceProxy);

// Generate a meal plan based on preferences
router.post('/generate', mealPlannerServiceProxy);

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

module.exports = router;