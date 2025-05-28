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
    console.log('[AUTH] No token provided in request');
    return res.status(401).json({ message: 'Authentication required' });
  }

  try {
    // If token is using older dummy format, reject it
    if (token.startsWith('dummy_token_')) {
      console.error('[AUTH] Deprecated token format used');
      return res.status(401).json({ message: 'Token format deprecated, please log in again' });
    }

    // Log token info for debugging (but don't log the full token for security)
    console.log(`[AUTH] Verifying token: ${token.substring(0, 15)}...`);
    console.log(`[AUTH] Using secret: ${JWT_SECRET.substring(0, 5)}...`);
    
    // Verify token with more debugging
    try {
      const decoded = jwt.verify(token, JWT_SECRET);
      
      // Log successful verification
      console.log(`[AUTH] Token verified successfully for user id: ${decoded.id}, role: ${decoded.role}`);
      
      // Add user data to request
      req.user = decoded;
      
      next();
    } catch (jwtError) {
      console.error('[AUTH] JWT verification failed:', jwtError.message);
      // Try to decode without verification to see what's in the token
      try {
        const decodedWithoutVerify = jwt.decode(token);
        console.log('[AUTH] Token contents without verification:', decodedWithoutVerify);
      } catch (e) {
        console.error('[AUTH] Could not decode token without verification');
      }
      
      return res.status(403).json({ message: 'Invalid or expired token: ' + jwtError.message });
    }
  } catch (error) {
    console.error('[AUTH] Token validation error:', error);
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
  
  // Log for debugging
  console.log('[AUTH] isSameUser middleware check:', {
    requestedUserId: userId,
    currentUserId: req.user ? req.user.id : 'not authenticated',
    userRole: req.user ? req.user.role : 'none'
  });

  // Convert IDs to strings for comparison to handle numeric vs string IDs
  const requestedId = String(userId);
  const currentUserId = req.user ? String(req.user.id) : null;
  
  // Allow if admin role OR if accessing own data
  if (req.user && (currentUserId === requestedId || req.user.role === 'admin')) {
    console.log('[AUTH] Access granted - same user or admin');
    next();
  } else {
    console.log('[AUTH] Access denied - user ID mismatch or not admin');
    return res.status(403).json({ 
      message: 'Access denied: You can only access your own data',
      requested: requestedId,
      current: currentUserId
    });
  }
};

module.exports = { authenticateToken, authorize, isAdmin, isSameUser };