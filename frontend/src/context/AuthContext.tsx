import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import jwtDecode from 'jwt-decode';
import { useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();

  useEffect(() => {
    const checkTokenAndSetUser = () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const decoded = jwtDecode<User & { exp: number }>(token);
          
          // Check if token is expired
          const currentTime = Date.now() / 1000;
          if (decoded.exp < currentTime) {
            // Token expired
            localStorage.removeItem('token');
            setUser(null);
          } else {
            // Valid token
            setUser({
              id: decoded.id,
              email: decoded.email,
              name: decoded.name,
              role: decoded.role
            });
          }
        } catch (error) {
          console.error('Invalid token', error);
          localStorage.removeItem('token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkTokenAndSetUser();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      const data = await authService.login(email, password);
      localStorage.setItem('token', data.token);
      
      const decoded = jwtDecode<User>(data.token);
      setUser({
        id: decoded.id,
        email: decoded.email,
        name: decoded.name,
        role: decoded.role
      });
      
      navigate('/dashboard');
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
      navigate('/login');
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
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};