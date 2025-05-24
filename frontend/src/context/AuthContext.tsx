import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import jwtDecode from 'jwt-decode';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../services/authService';

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

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isNewUser, setIsNewUser] = useState(false);
  const [hasCompletedPreferences, setHasCompletedPreferences] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const checkTokenAndSetUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          // For static tokens, manually create the user object
          if (token.startsWith('dummy_token_')) {
            const userId = token.replace('dummy_token_', '');
            // Try to fetch the user profile
            try {
              const userProfile = await authService.getUserProfile(userId);
              setUser({
                id: userId,
                email: userProfile.user.email,
                name: userProfile.user.name,
                role: 'user'
              });
            } catch (error) {
              console.error('Error fetching user profile:', error);
              localStorage.removeItem('token');
              setUser(null);
            }
          } else {
            // Try to parse JWT token
            try {
              const decoded = jwtDecode<User & { exp: number }>(token);
              
              // Check if token is expired
              const currentTime = Date.now() / 1000;
              if (decoded.exp && decoded.exp < currentTime) {
                // Token expired
                localStorage.removeItem('token');
                setUser(null);
              } else {
                // Valid token
                const userData = {
                  id: decoded.id,
                  email: decoded.email,
                  name: decoded.name,
                  role: decoded.role || 'user'
                };
                setUser(userData);
                
                // Check if user has preferences
                try {
                  const userProfile = await authService.getUserProfile(userData.id);
                  // Consider preferences completed if any preferences exist
                  const hasPrefs = userProfile.preferences && 
                    (userProfile.preferences.allergies?.length > 0 || 
                     userProfile.preferences.preferred_cuisines?.length > 0 ||
                     userProfile.preferences.disliked_ingredients?.length > 0 ||
                     (userProfile.preferences.preferences?.dietary_restrictions?.length > 0));
                  
                  setHasCompletedPreferences(hasPrefs);
                } catch (error) {
                  console.error('Error checking user preferences', error);
                }
              }
            } catch (error) {
              console.error('Invalid token, falling back to basic user data', error);
              
              // If JWT parsing fails, still try to use the token as a plain token
              // This is a fallback mechanism for development
              try {
                await authService.getCurrentUser(); // This will use the token to get current user
              } catch (e) {
                console.error('Could not get current user with token, logging out');
                localStorage.removeItem('token');
                setUser(null);
              }
            }
          }
        } catch (error) {
          console.error('Error processing token:', error);
          localStorage.removeItem('token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkTokenAndSetUser();
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
        
        // Set user directly from response instead of trying to decode the token
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
          // Consider preferences completed if any preferences exist
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