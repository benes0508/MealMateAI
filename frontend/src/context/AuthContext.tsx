import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import jwtDecode from 'jwt-decode';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../services/authService';
import axios from 'axios';

type User = {
  id: string;
  email: string;
  name: string;
  role: string;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isNewUser: boolean;
  setIsNewUser: (isNew: boolean) => void;
  hasCompletedPreferences: boolean;
  setHasCompletedPreferences: (completed: boolean) => void;
  setUser: (user: User | null) => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

type AuthProviderProps = {
  children: ReactNode;
};

// Setup axios interceptor for token refresh
const setupAxiosInterceptors = () => {
  // Remove existing interceptors to avoid duplicates
  axios.interceptors.response.eject(axios.interceptors.response.handlers?.[0]);

  axios.interceptors.response.use(
    response => response,
    error => {
      // Only handle auth errors (401) automatically
      // Don't log out for 403 errors as they could be permission related
      if (error.response && error.response.status === 401) {
        console.warn('Unauthorized request detected (401). Logging out.');
        localStorage.removeItem('token');
        delete axios.defaults.headers.common['Authorization'];
        
        // Use window.location for hard redirect only if it's not an API check
        // This prevents logout loops during authentication checks
        const isAuthCheck = error.config.url.includes('/api/users/me');
        if (!isAuthCheck) {
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
  );
};

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isNewUser, setIsNewUser] = useState(false);
  const [hasCompletedPreferences, setHasCompletedPreferences] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Setup axios interceptors once on component mount
  useEffect(() => {
    setupAxiosInterceptors();
  }, []);

  // This function will try to restore the user session from the JWT token
  useEffect(() => {
    const checkTokenAndSetUser = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          console.log('No token found in localStorage');
          setLoading(false);
          return;
        }

        // Set authorization header for all future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

        // First check if we can extract user data directly from token
        try {
          // Decode the JWT token to get user data
          const decoded = jwtDecode<any>(token);
          console.log('Token decoded successfully');
          
          // Check token expiration
          const currentTime = Date.now() / 1000;
          if (decoded.exp && decoded.exp < currentTime) {
            console.warn('Token has expired. Logging out.');
            localStorage.removeItem('token');
            delete axios.defaults.headers.common['Authorization'];
            setLoading(false);
            return;
          }
          
          // Set user data from token while we wait for the API
          // This gives instant authentication on page load
          if (decoded.id) {
            console.log('Setting user from decoded token');
            setUser({
              id: decoded.id,
              email: decoded.email || '',
              name: decoded.name || '',
              role: decoded.role || 'user'
            });
            
            // Critical change: We are now authenticated even if API fails
            // This ensures the user stays logged in even if API is temporarily unavailable
          }
        } catch (e) {
          console.error('Failed to decode token:', e);
          // Continue to API fallback
        }

        // Try to fetch user data from API
        try {
          console.log('Fetching current user data from API');
          const currentUser = await authService.getCurrentUser();
          
          if (currentUser) {
            console.log('User data successfully fetched from API');
            // Update with full user data from API
            setUser({
              id: currentUser.id,
              email: currentUser.email,
              name: currentUser.name,
              role: currentUser.role || 'user'
            });
  
            // Check if user has preferences
            try {
              const userProfile = await authService.getUserProfile(currentUser.id);
              const hasPrefs = userProfile.preferences && 
                (userProfile.preferences.allergies?.length > 0 || 
                userProfile.preferences.preferred_cuisines?.length > 0 ||
                userProfile.preferences.disliked_ingredients?.length > 0 ||
                (userProfile.preferences.preferences?.dietary_restrictions?.length > 0));
              
              setHasCompletedPreferences(hasPrefs);
            } catch (error) {
              console.error('Error checking user preferences, but continuing session:', error);
              // Don't clear auth - just log the error
            }
          }
        } catch (apiError) {
          // If API call fails but we have user data from token,
          // don't log out - just keep using the token data
          console.error('API user fetch failed, using token data instead:', apiError);
          
          // Only clear auth if we don't have user data from token
          if (!user) {
            console.warn('No user data from token or API - logging out');
            localStorage.removeItem('token');
            delete axios.defaults.headers.common['Authorization'];
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Error in authentication check:', error);
        // Don't clear token yet unless it's clearly invalid
      } finally {
        setLoading(false);
      }
    };

    checkTokenAndSetUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Check URL for newUser param on page load
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const newUserParam = queryParams.get('newUser');
    
    if (newUserParam === 'true') {
      setIsNewUser(true);
    }
  }, [location]);

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      const data = await authService.login({ email, password });
      
      if (data.token) {
        localStorage.setItem('token', data.token);
        
        // Set axios default authorization header
        axios.defaults.headers.common['Authorization'] = `Bearer ${data.token}`;
        
        // Set user directly from response
        const userData = {
          id: data.user.id,
          email: data.user.email,
          name: data.user.name,
          role: data.user.role || 'user'
        };
        
        setUser(userData);
        
        // Check if user has preferences
        try {
          const userProfile = await authService.getUserProfile(userData.id);
          
          const hasPrefs = userProfile.preferences && 
            (userProfile.preferences.allergies?.length > 0 || 
             userProfile.preferences.preferred_cuisines?.length > 0 ||
             userProfile.preferences.disliked_ingredients?.length > 0 ||
             (userProfile.preferences.preferences?.dietary_restrictions?.length > 0));
          
          setHasCompletedPreferences(hasPrefs);
          
          // If new user without preferences, redirect to preference setup
          if (isNewUser && !hasPrefs) {
            navigate('/preference-setup');
          } else {
            navigate('/dashboard');
          }
        } catch (error) {
          console.error('Error checking user preferences', error);
          navigate('/dashboard');
        }
      } else {
        throw new Error('Login response did not include a token');
      }
    } catch (error) {
      console.error('Login error', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (name: string, email: string, password: string) => {
    try {
      setLoading(true);
      await authService.register(name, email, password);
      setIsNewUser(true); // Set new user flag
      navigate('/login?newUser=true'); // Add query param to indicate new registration
    } catch (error) {
      console.error('Registration error', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setIsNewUser(false);
    setHasCompletedPreferences(false);
    navigate('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
        isNewUser,
        setIsNewUser,
        hasCompletedPreferences,
        setHasCompletedPreferences,
        setUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};