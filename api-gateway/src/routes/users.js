// src/routes/users.js

const express = require('express');
const { authenticateToken, isSameUser, isAdmin } = require('../middleware/auth');
const { createServiceProxy } = require('../utils/proxy');

const router = express.Router();

// Create a proxy to the user service
const userServiceProxy = createServiceProxy('users');

// Public routes
router.post('/login', userServiceProxy);
router.post('/register', userServiceProxy);

// Protected routes that require authentication
router.use(authenticateToken);

// Routes that require users to access only their own data
router.get('/:id', isSameUser, userServiceProxy);
router.put('/:id', isSameUser, userServiceProxy);
router.delete('/:id', isSameUser, userServiceProxy);

// Get user preferences
router.get('/:id/preferences', isSameUser, userServiceProxy);
router.put('/:id/preferences', isSameUser, userServiceProxy);

// Admin-only routes
router.get('/', isAdmin, userServiceProxy);

module.exports = router;