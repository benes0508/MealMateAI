import axios from 'axios';

// Use relative URL for browser requests - this will be handled by Nginx proxy
const API_URL = '/api'; // Changed from hardcoded Docker service URL

export interface User {
  id: string;
  name: string;
  email: string;
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

const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await axios.post(`${API_URL}/users/login`, credentials);
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
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
      const response = await axios.post(`${API_URL}/users/register/simple`, userData);
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
      const response = await axios.get(`${API_URL}/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      throw error;
    }
  },

  async updateUserProfile(userId: string, data: UpdateProfileData): Promise<User> {
    try {
      const response = await axios.put(`${API_URL}/users/${userId}`, data);
      return response.data.user;
    } catch (error) {
      console.error('Error updating profile:', error);
      throw error;
    }
  },

  async updateUserPreferences(userId: string, preferences: UserPreferences): Promise<UserPreferences> {
    try {
      const response = await axios.put(`${API_URL}/users/${userId}/preferences`, preferences);
      return response.data.preferences;
    } catch (error) {
      console.error('Error updating preferences:', error);
      throw error;
    }
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        return null;
      }
      
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      const response = await axios.get(`${API_URL}/users/me`);
      return response.data.user;
    } catch (error) {
      console.error('Error getting current user:', error);
      this.logout();
      return null;
    }
  },

  logout(): void {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  },

  async deleteAccount(userId: string): Promise<void> {
    try {
      await axios.delete(`${API_URL}/users/${userId}`);
      this.logout();
    } catch (error) {
      console.error('Error deleting account:', error);
      throw error;
    }
  }
};

export default authService;