// src/services/ml.js
import { API_BASE_URL } from '../utils/api';
import { getToken } from './auth';

/**
 * ML service for interacting with machine learning functionality
 */

/**
 * Helper function to make authenticated requests
 * 
 * @param {string} endpoint - API endpoint to call
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} - JSON response
 */
const authFetch = async (endpoint, options = {}) => {
  const token = getToken();
  
  if (!token) {
    throw new Error('Authentication required');
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers
    }
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.message || 'API request failed');
  }
  
  return data;
};

/**
 * Extract keywords from a project's citations
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Object>} - Extracted keywords
 */
export const extractKeywords = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}/extract-keywords`);
    return {
      includeKeywords: data.include_keywords || [],
      excludeKeywords: data.exclude_keywords || []
    };
  } catch (error) {
    console.error(`Error extracting keywords for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Get initial citations for review
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Array>} - Initial citations for review
 */
export const getInitialCitations = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}/initial-citations`);
    return data.citations;
  } catch (error) {
    console.error(`Error getting initial citations for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Train the ML model with selected citations
 * 
 * @param {number|string} projectId - ID of the project
 * @param {Object} selections - User selections
 * @param {Array<number>} selections.relevant_ids - IDs of relevant citations
 * @param {Array<number>} selections.irrelevant_ids - IDs of irrelevant citations
 * @returns {Promise<Object>} - Training results
 */
export const trainModel = async (projectId, selections) => {
  try {
    const data = await authFetch(`/projects/${projectId}/train`, {
      method: 'POST',
      body: JSON.stringify(selections)
    });
    
    return data;
  } catch (error) {
    console.error(`Error training model for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Get sorted citations based on relevance score
 * 
 * @param {number|string} projectId - ID of the project
 * @param {Object} options - Sorting options
 * @param {string} options.sort - Sort order ('desc' or 'asc')
 * @param {number} options.limit - Maximum number of citations to return
 * @returns {Promise<Array>} - Sorted citations
 */
export const getSortedCitations = async (projectId, options = {}) => {
  try {
    const queryParams = new URLSearchParams();
    if (options.sort) queryParams.append('sort', options.sort);
    if (options.limit) queryParams.append('limit', options.limit);
    
    const data = await authFetch(`/projects/${projectId}/citations?${queryParams.toString()}`);
    return data.citations;
  } catch (error) {
    console.error(`Error getting sorted citations for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Get the next batch of citations for review
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Object>} - Next batch of citations
 */
export const getNextCitationBatch = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}/next-batch`);
    return {
      topCitations: data.top_citations || [],
      bottomCitations: data.bottom_citations || [],
      currentIteration: data.current_iteration
    };
  } catch (error) {
    console.error(`Error getting next citation batch for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Toggle citation relevance (for manual labeling)
 * 
 * @param {number|string} projectId - ID of the project
 * @param {number|string} citationId - ID of the citation
 * @param {boolean} isRelevant - Whether the citation is relevant
 * @returns {Promise<Object>} - Updated citation
 */
export const toggleCitationRelevance = async (projectId, citationId, isRelevant) => {
  try {
    const data = await authFetch(`/projects/${projectId}/citations/${citationId}/toggle-relevance`, {
      method: 'POST',
      body: JSON.stringify({ is_relevant: isRelevant })
    });
    
    return data;
  } catch (error) {
    console.error(`Error toggling relevance for citation ${citationId}:`, error);
    throw error;
  }
};

/**
 * Export citations to a file
 * 
 * @param {number|string} projectId - ID of the project
 * @param {Object} options - Export options
 * @param {string} options.format - File format ('csv' or 'excel')
 * @param {number|string} options.limit - Number of citations to export ('all' or a number)
 * @returns {Promise<string>} - URL to download the exported file
 */
export const exportCitations = async (projectId, options = {}) => {
  try {
    const token = getToken();
    
    if (!token) {
      throw new Error('Authentication required');
    }
    
    const queryParams = new URLSearchParams();
    if (options.format) queryParams.append('format', options.format);
    if (options.limit && options.limit !== 'all') queryParams.append('limit', options.limit);
    
    const url = `${API_BASE_URL}/projects/${projectId}/export?${queryParams.toString()}`;
    
    // For file downloads, we don't parse the response as JSON
    // Instead, we redirect the browser to the download URL
    window.open(url, '_blank');
    
    // Return the URL in case the caller wants to handle the download differently
    return url;
  } catch (error) {
    console.error(`Error exporting citations for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Analyze keyword effectiveness
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Object>} - Keyword effectiveness analysis
 */
export const analyzeKeywordEffectiveness = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}/analyze-keywords`);
    return data;
  } catch (error) {
    console.error(`Error analyzing keywords for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Get citation statistics
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Object>} - Citation statistics
 */
export const getCitationStats = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}/stats`);
    return data.citation_stats;
  } catch (error) {
    console.error(`Error getting citation stats for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Get training iteration history
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Array>} - Training iteration history
 */
export const getTrainingHistory = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}/iterations`);
    return data.iterations;
  } catch (error) {
    console.error(`Error getting training history for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Get download options for project
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Object>} - Download options
 */
export const getDownloadOptions = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}/download-options`);
    return {
      options: data.options || [],
      formats: data.formats || []
    };
  } catch (error) {
    console.error(`Error getting download options for project ${projectId}:`, error);
    throw error;
  }
};