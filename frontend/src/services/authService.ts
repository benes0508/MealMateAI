import axios from 'axios';
import jwtDecode from 'jwt-decode';

// Use relative URL for browser requests
const API_URL = '/api';

// Define max token expiry for fallback (7 days)
const MAX_TOKEN_AGE = 7 * 24 * 60 * 60; // seconds

export interface User {
  id: string;
  name: string;
  email: string;
  role?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserPreferences {
  dietaryRestrictions: {
    vegetarian: boolean;
    vegan: boolean;
    glutenFree: boolean;
    dairyFree: boolean;
    nutFree: boolean;
    keto: boolean;
    paleo: boolean;
  };
  allergies: string[];
  dislikedIngredients: string[];
  favoriteIngredients: string[];
  calorieTarget: string;
  cookingSkill: 'beginner' | 'intermediate' | 'advanced';
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}

export interface UpdateProfileData {
  name?: string;
  email?: string;
  current_password?: string;
  new_password?: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

// Initialize authorization header from localStorage if token exists
const initializeAuthHeader = () => {
  const token = localStorage.getItem('token');
  if (token) {
    // Check if token is expired before setting it
    try {
      const decoded = jwtDecode<any>(token);
      const currentTime = Date.now() / 1000;
      
      // If token has expiry and is not expired, set it
      if (!decoded.exp || decoded.exp > currentTime) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        console.log('Authorization header initialized from stored token');
      } else {
        console.warn('Stored token is expired, removing it');
        localStorage.removeItem('token');
      }
    } catch (e) {
      console.error('Failed to decode stored token:', e);
      // Keep token in storage but don't use it for requests
    }
  }
};

// Call this when the service is first loaded
initializeAuthHeader();

const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await axios.post(`${API_URL}/users/login`, credentials);
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
        console.log('Login successful, token stored');
        
        // Add token expiry check
        try {
          const decoded = jwtDecode<any>(response.data.token);
          if (!decoded.exp) {
            console.warn('Token has no expiration - using default max age');
            const currentTime = Math.floor(Date.now() / 1000);
            // Store last login time to allow fallback expiry check
            localStorage.setItem('login_timestamp', currentTime.toString());
          }
        } catch (e) {
          console.error('Could not decode token for expiry check:', e);
        }
      }
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  async register(nameOrData: string | RegisterData, email?: string, password?: string): Promise<AuthResponse> {
    try {
      let userData: any;
      
      // Handle both parameter styles
      if (typeof nameOrData === 'object') {
        // Called with a data object
        userData = {
          email: nameOrData.email,
          username: nameOrData.email?.includes('@') ? nameOrData.email.split('@')[0] : `user_${Date.now()}`,
          full_name: nameOrData.name || '',
          password: nameOrData.password || '',
          allergies: [],
          disliked_ingredients: [],
          preferred_cuisines: [],
          preferences: {}
        };
      } else {
        // Called with individual parameters
        if (!email) {
          throw new Error('Email is required for registration');
        }
        
        userData = {
          email: email,
          username: email.includes('@') ? email.split('@')[0] : `user_${Date.now()}`,
          full_name: nameOrData || '',
          password: password || '',
          allergies: [],
          disliked_ingredients: [],
          preferred_cuisines: [],
          preferences: {}
        };
      }
      
      // Use the simplified registration endpoint to avoid body reading issues
      console.log("Sending registration request:", userData);
      const response = await axios.post(`${API_URL}/users/register`, userData);
      console.log("Registration response:", response.data);
      
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
      }
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },

  async getUserProfile(userId: string): Promise<{ user: User; preferences: UserPreferences }> {
    try {
      // Ensure header is set before each request
      this.ensureAuthHeader();
      
      const response = await axios.get(`${API_URL}/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      throw error;
    }
  },

  async updateUserProfile(userId: string, data: UpdateProfileData): Promise<User> {
    try {
      // Ensure header is set before each request
      this.ensureAuthHeader();
      
      const response = await axios.put(`${API_URL}/users/${userId}`, data);
      return response.data.user;
    } catch (error) {
      console.error('Error updating profile:', error);
      throw error;
    }
  },

  async updateUserPreferences(userId: string, preferences: UserPreferences): Promise<UserPreferences> {
    try {
      // Ensure header is set before each request
      this.ensureAuthHeader();
      
      const response = await axios.put(`${API_URL}/users/${userId}/preferences`, preferences);
      return response.data.preferences;
    } catch (error) {
      console.error('Error updating preferences:', error);
      throw error;
    }
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      // Check if token exists and isn't expired
      if (!this.isValidToken()) {
        console.log('No valid token for getCurrentUser');
        return null;
      }
      
      // Ensure header is set before request
      this.ensureAuthHeader();
      
      const response = await axios.get(`${API_URL}/users/me`);
      return response.data.user;
    } catch (error) {
      console.error('Error getting current user:', error);
      
      // Only logout on clear auth errors
      if (error.response && error.response.status === 401) {
        console.warn('Unauthorized (401), clearing authentication');
        this.logout();
      } else {
        // For other errors, don't logout automatically
        console.warn('API error, but not clearing authentication');
      }
      return null;
    }
  },

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('login_timestamp');
    delete axios.defaults.headers.common['Authorization'];
    console.log('User logged out, auth cleared');
  },

  async deleteAccount(userId: string): Promise<void> {
    try {
      // Ensure header is set before request
      this.ensureAuthHeader();
      
      await axios.delete(`${API_URL}/users/${userId}`);
      this.logout();
    } catch (error) {
      console.error('Error deleting account:', error);
      throw error;
    }
  },
  
  // Helper methods for token management
  
  // Check if the current token is valid
  isValidToken(): boolean {
    const token = localStorage.getItem('token');
    if (!token) return false;
    
    try {
      const decoded = jwtDecode<any>(token);
      const currentTime = Date.now() / 1000;
      
      // Check explicit expiry if available
      if (decoded.exp) {
        return decoded.exp > currentTime;
      }
      
      // Fall back to login timestamp + MAX_TOKEN_AGE
      const loginTimestamp = parseInt(localStorage.getItem('login_timestamp') || '0', 10);
      if (loginTimestamp > 0) {
        return (loginTimestamp + MAX_TOKEN_AGE) > currentTime;
      }
      
      // If no way to check expiry, assume token is valid
      return true;
    } catch (e) {
      console.error('Error checking token validity:', e);
      // Don't invalidate token on parse error
      return true;
    }
  },
  
  // Ensure the Authorization header is set if token exists
  ensureAuthHeader(): void {
    const token = localStorage.getItem('token');
    if (token && this.isValidToken()) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  },
  
  // Check if the user is authenticated based on token existence and validity
  isAuthenticated(): boolean {
    return this.isValidToken();
  },
  
  // Get the token from localStorage
  getToken(): string | null {
    return localStorage.getItem('token');
  }
};

export default authService;