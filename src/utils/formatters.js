/**
 * Format a date string to a readable format
 * @param {string} dateString - The date string to format
 * @returns {string} - The formatted date string
 */
export const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      console.error('Error formatting date:', error);
      return dateString;
    }
  };
  
  /**
   * Truncate a string to a maximum length
   * @param {string} str - The string to truncate
   * @param {number} maxLength - The maximum length
   * @returns {string} - The truncated string
   */
  export const truncateString = (str, maxLength = 100) => {
    if (!str) return '';
    
    if (str.length <= maxLength) {
      return str;
    }
    
    return str.substring(0, maxLength) + '...';
  };
  
  // src/utils/validators.js
  
  /**
   * Validate an email address
   * @param {string} email - The email to validate
   * @returns {boolean} - Whether the email is valid
   */
  export const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };
  
  /**
   * Validate a password (minimum 6 characters)
   * @param {string} password - The password to validate
   * @returns {boolean} - Whether the password is valid
   */
  export const isValidPassword = (password) => {
    return password && password.length >= 6;
  };
  
  /**
   * Validate that a field is not empty
   * @param {string} value - The value to validate
   * @returns {boolean} - Whether the value is not empty
   */
  export const isNotEmpty = (value) => {
    return value && value.trim().length > 0;
  };
  