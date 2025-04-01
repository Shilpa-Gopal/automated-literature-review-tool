// src/utils/api.js

// API base URL - read from environment or use default
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

/**
 * Make an API request with appropriate error handling
 * 
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {Object} options - Fetch options
 * @returns {Promise<any>} - Parsed JSON response
 */
export const apiRequest = async (endpoint, options = {}) => {
  try {
    // Get auth token if available
    const token = localStorage.getItem('token');
    
    // Set up headers
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    // Add authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Construct full URL
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Log request in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Request: ${options.method || 'GET'} ${url}`);
    }
    
    // Make the request
    const response = await fetch(url, {
      ...options,
      headers
    });
    
    // Parse response as JSON
    let data;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      // Handle non-JSON responses
      const text = await response.text();
      data = { message: text };
    }
    
    // Handle error responses
    if (!response.ok) {
      throw new Error(data.message || response.statusText || 'API request failed');
    }
    
    return data;
  } catch (error) {
    // Log error in development
    if (process.env.NODE_ENV === 'development') {
      console.error('API request failed:', error);
    }
    
    // Handle authentication errors
    if (error.message.includes('Authentication required') || 
        error.message.includes('token expired') ||
        error.message.includes('Invalid token')) {
      // Clear authentication state
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('isLoggedIn');
      
      // Redirect to login page
      window.location.href = '/login';
    }
    
    throw error;
  }
};

/**
 * Upload a file to the API
 * 
 * @param {string} endpoint - API endpoint
 * @param {File} file - File to upload
 * @param {Object} additionalFormData - Additional form data to include
 * @param {Object} options - Additional fetch options
 * @returns {Promise<any>} - Response data
 */
export const uploadFile = async (endpoint, file, additionalFormData = {}, options = {}) => {
  try {
    // Get auth token if available
    const token = localStorage.getItem('token');
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    // Add any additional form data
    Object.entries(additionalFormData).forEach(([key, value]) => {
      formData.append(key, value);
    });
    
    // Set up headers (without Content-Type as it's set automatically for FormData)
    const headers = { ...options.headers };
    
    // Add authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Construct full URL
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Make the request
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      headers,
      ...options
    });
    
    // Parse response
    let data;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      data = { message: text };
    }
    
    // Handle error responses
    if (!response.ok) {
      throw new Error(data.message || response.statusText || 'File upload failed');
    }
    
    return data;
  } catch (error) {
    console.error('File upload failed:', error);
    throw error;
  }
};

/**
 * Download a file from the API
 * 
 * @param {string} endpoint - API endpoint
 * @param {string} filename - Filename to save as
 * @param {Object} options - Additional fetch options
 */
export const downloadFile = async (endpoint, filename, options = {}) => {
  try {
    // Get auth token if available
    const token = localStorage.getItem('token');
    
    // Set up headers
    const headers = { ...options.headers };
    
    // Add authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Construct full URL
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Make the request
    const response = await fetch(url, {
      ...options,
      headers
    });
    
    // Handle error responses
    if (!response.ok) {
      let errorMessage;
      try {
        const errorData = await response.json();
        errorMessage = errorData.message;
      } catch (e) {
        errorMessage = response.statusText || 'File download failed';
      }
      throw new Error(errorMessage);
    }
    
    // Get the blob data
    const blob = await response.blob();
    
    // Create a download link
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    
    // Append to the document, click, and remove
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up the URL object
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('File download failed:', error);
    throw error;
  }
};