// src/routes/users.js

const express = require('express');
const { authenticateToken, isSameUser, isAdmin } = require('../middleware/auth');
const { createServiceProxy } = require('../utils/proxy');
const axios = require('axios');
const { USER_SERVICE_URL } = require('../config/config');

const router = express.Router();

// Create a proxy to the user service
const userServiceProxy = createServiceProxy('users');

// Handle registration directly instead of proxying
router.post('/register', async (req, res) => {
  try {
    console.log('[API-GATEWAY] Registration request received:', req.body);
    
    // Forward the request to user service manually instead of using proxy
    const response = await axios.post(`${USER_SERVICE_URL}/register/simple`, req.body, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    console.log('[API-GATEWAY] Registration response received:', response.data);
    
    // Return the response from user service
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error('[API-GATEWAY] Registration error:', error.message);
    if (error.response) {
      console.error('[API-GATEWAY] Error response from user service:', error.response.data);
      res.status(error.response.status).json(error.response.data);
    } else {
      res.status(500).json({ 
        message: 'Internal server error processing registration',
        error: error.message 
      });
    }
  }
});

// Handle login directly instead of proxying
router.post('/login', async (req, res) => {
  try {
    console.log('[API-GATEWAY] Login request received:');
    console.log('[API-GATEWAY] Login body:', JSON.stringify(req.body, null, 2));
    console.log('[API-GATEWAY] Login headers:', JSON.stringify(req.headers, null, 2));
    
    // Ensure we have proper email and password fields
    const loginData = {
      email: req.body.email,
      password: req.body.password
    };
    
    console.log('[API-GATEWAY] Formatted login data:', JSON.stringify(loginData, null, 2));
    
    if (!loginData.email || !loginData.password) {
      console.error('[API-GATEWAY] Missing email or password in login request');
      return res.status(400).json({ 
        message: 'Email and password are required'
      });
    }
    
    // Forward the request to user service's JSON login endpoint
    const response = await axios.post(`${USER_SERVICE_URL}/login/json`, loginData, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    console.log('[API-GATEWAY] Login response received:', JSON.stringify(response.data, null, 2));
    
    // Return the response from user service
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error('[API-GATEWAY] Login error:', error.message);
    if (error.response) {
      console.error('[API-GATEWAY] Error response status:', error.response.status);
      console.error('[API-GATEWAY] Error response from user service:', JSON.stringify(error.response.data, null, 2));
      res.status(error.response.status).json(error.response.data);
    } else {
      res.status(500).json({ 
        message: 'Internal server error processing login',
        error: error.message 
      });
    }
  }
});

// Public routes
router.post('/', userServiceProxy); // Add root POST endpoint for user creation/registration

// Protected routes that require authentication
router.use(authenticateToken);

// Current user endpoint
router.get('/me', async (req, res) => {
  try {
    // The user data comes from the JWT token, extracted in authenticateToken middleware
    if (!req.user || !req.user.id) {
      return res.status(401).json({ message: 'User not authenticated' });
    }
    
    console.log('[API-GATEWAY] Getting current user data for id:', req.user.id);
    
    // Forward the request to user service to get full user details
    const response = await axios.get(`${USER_SERVICE_URL}/${req.user.id}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Return the response from user service
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error('[API-GATEWAY] Error getting current user:', error.message);
    if (error.response) {
      res.status(error.response.status).json(error.response.data);
    } else {
      res.status(500).json({ 
        message: 'Internal server error getting current user',
        error: error.message 
      });
    }
  }
});

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