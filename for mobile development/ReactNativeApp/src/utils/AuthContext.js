import React, {createContext, useContext, useState, useEffect} from 'react';
import APIService from '../services/api';
import SecureStorage from 'react-native-secure-storage';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({children}) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on app start
    loadStoredToken();
  }, []);

  const loadStoredToken = async () => {
    try {
      const token = await SecureStorage.getItem('auth_token');
      if (token) {
        APIService.setToken(token);
        // Verify token is still valid
        const tokenInfo = await APIService.getTokenInfo();
        setUser(tokenInfo);
      }
    } catch (error) {
      console.log('No valid token found:', error);
      await SecureStorage.removeItem('auth_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await APIService.login(username, password);
      
      if (response.token) {
        APIService.setToken(response.token);
        await SecureStorage.setItem('auth_token', response.token);
        setUser(response);
        return {success: true};
      } else {
        return {success: false, error: 'No token received'};
      }
    } catch (error) {
      return {
        success: false,
        error: error.message || 'Login failed',
      };
    }
  };

  const logout = async () => {
    try {
      await APIService.logout();
    } catch (error) {
      console.log('Logout API call failed:', error);
    } finally {
      APIService.clearToken();
      await SecureStorage.removeItem('auth_token');
      setUser(null);
    }
  };

  const refreshToken = async () => {
    try {
      const response = await APIService.refreshToken();
      if (response.token) {
        APIService.setToken(response.token);
        await SecureStorage.setItem('auth_token', response.token);
        setUser(response);
        return {success: true};
      }
      return {success: false, error: 'Token refresh failed'};
    } catch (error) {
      await logout();
      return {
        success: false,
        error: error.message || 'Token refresh failed',
      };
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    refreshToken,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
