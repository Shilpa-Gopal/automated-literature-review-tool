// src/services/auth.js
import { API_BASE_URL } from '../utils/api';

/**
 * Authentication service for handling user authentication operations
 */

/**
 * Register a new user
 * 
 * @param {Object} userData - User registration data
 * @param {string} userData.firstName - User's first name
 * @param {string} userData.lastName - User's last name
 * @param {string} userData.email - User's email
 * @param {string} userData.password - User's password
 * @param {string} userData.institution - User's institution (optional)
 * @returns {Promise<Object>} - Response from the server
 */
export const register = async (userData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Registration failed');
    }

    return data;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

/**
 * Log in a user
 * 
 * @param {Object} credentials - User login credentials
 * @param {string} credentials.email - User's email
 * @param {string} credentials.password - User's password
 * @returns {Promise<Object>} - Response from the server including auth token
 */
export const login = async (credentials) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Login failed');
    }

    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

/**
 * Log out the current user
 * Removes token from local storage
 */
export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('isLoggedIn');
};

/**
 * Get the current authenticated user's profile
 * 
 * @returns {Promise<Object>} - User profile data
 */
export const getCurrentUser = async () => {
  try {
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/auth/profile`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to get user profile');
    }

    return data.user;
  } catch (error) {
    console.error('Get user profile error:', error);
    throw error;
  }
};

/**
 * Update the current user's profile
 * 
 * @param {Object} userData - Updated user data
 * @returns {Promise<Object>} - Updated user profile
 */
export const updateProfile = async (userData) => {
  try {
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/auth/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(userData)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to update profile');
    }

    return data.user;
  } catch (error) {
    console.error('Update profile error:', error);
    throw error;
  }
};

/**
 * Change the user's password
 * 
 * @param {Object} passwordData - Password change data
 * @param {string} passwordData.currentPassword - Current password
 * @param {string} passwordData.newPassword - New password
 * @returns {Promise<Object>} - Response from the server
 */
export const changePassword = async (passwordData) => {
  try {
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(passwordData)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Failed to change password');
    }

    return data;
  } catch (error) {
    console.error('Change password error:', error);
    throw error;
  }
};

/**
 * Check if the user is authenticated
 * 
 * @returns {boolean} - True if user is authenticated
 */
export const isAuthenticated = () => {
  return localStorage.getItem('isLoggedIn') === 'true' && !!localStorage.getItem('token');
};

/**
 * Get the authentication token
 * 
 * @returns {string|null} - Authentication token or null if not authenticated
 */
export const getToken = () => {
  return localStorage.getItem('token');
};