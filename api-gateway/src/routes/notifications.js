// src/routes/notifications.js

const express = require('express');
const { authenticateToken, isSameUser, isAdmin } = require('../middleware/auth');
const { createServiceProxy } = require('../utils/proxy');

const router = express.Router();

// Create a proxy to the notification service
const notificationServiceProxy = createServiceProxy('notifications');

// All notification routes require authentication
router.use(authenticateToken);

// Get user notifications
router.get('/user/:userId', isSameUser, notificationServiceProxy);

// Mark a notification as read
router.put('/:id/read', notificationServiceProxy);

// Mark all user notifications as read
router.put('/user/:userId/read-all', isSameUser, notificationServiceProxy);

// Update notification preferences
router.put('/user/:userId/preferences', isSameUser, notificationServiceProxy);

// Get notification preferences
router.get('/user/:userId/preferences', isSameUser, notificationServiceProxy);

// Admin routes
router.post('/broadcast', isAdmin, notificationServiceProxy);
router.get('/stats', isAdmin, notificationServiceProxy);

module.exports = router;