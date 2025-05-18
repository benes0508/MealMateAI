// src/middleware/auth.js

const jwt = require('jsonwebtoken');
const { JWT_SECRET } = require('../config/config');

/**
 * JWT Authentication middleware
 * Verifies the token and adds the decoded user to the request object
 */
const authenticateToken = async (req, res, next) => {
  // Get auth header
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN format
  
  if (!token) {
    return res.status(401).json({ message: 'Authentication required' });
  }

  try {
    // Verify token
    const decoded = jwt.verify(token, JWT_SECRET);
    
    // Add user data to request
    req.user = decoded;
    
    next();
  } catch (error) {
    console.error('Token validation error:', error);
    return res.status(403).json({ message: 'Invalid or expired token' });
  }
};

/**
 * Role-based authorization middleware
 * Checks if the user has the required role(s)
 * @param {string|string[]} roles - The role(s) required to access the resource
 */
const authorize = (roles = []) => {
  // Convert string to array if only one role is provided
  if (typeof roles === 'string') {
    roles = [roles];
  }

  return (req, res, next) => {
    // Check if user exists and has role property
    if (!req.user || !req.user.role) {
      return res.status(403).json({ message: 'Forbidden' });
    }

    // Check if user's role is in the required roles
    if (roles.length && !roles.includes(req.user.role)) {
      return res.status(403).json({ message: 'Forbidden: insufficient permissions' });
    }

    // User has required role, proceed
    next();
  };
};

// Middleware to check if user is admin
const isAdmin = (req, res, next) => {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).json({ message: 'Admin access required' });
  }
  next();
};

// Middleware to ensure user can only access their own data
const isSameUser = (req, res, next) => {
  const userId = req.params.userId || req.params.id;
  
  if (!req.user || (req.user.id !== userId && req.user.role !== 'admin')) {
    return res.status(403).json({ message: 'Access denied' });
  }
  next();
};

module.exports = { authenticateToken, authorize, isAdmin, isSameUser };