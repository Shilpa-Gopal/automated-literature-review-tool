// src/services/project.js
import { API_BASE_URL } from '../utils/api';
import { getToken } from './auth';

/**
 * Project service for managing literature review projects
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
 * Get all projects for the current user
 * 
 * @returns {Promise<Array>} - List of projects
 */
export const getProjects = async () => {
  try {
    const data = await authFetch('/projects');
    return data.projects;
  } catch (error) {
    console.error('Error getting projects:', error);
    throw error;
  }
};

/**
 * Get a specific project by ID
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Object>} - Project details
 */
export const getProject = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}`);
    return data.project;
  } catch (error) {
    console.error(`Error getting project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Create a new project
 * 
 * @param {Object} projectData - Project data
 * @param {string} projectData.name - Project name
 * @param {string} projectData.description - Project description (optional)
 * @returns {Promise<Object>} - Created project
 */
export const createProject = async (projectData) => {
  try {
    const data = await authFetch('/projects', {
      method: 'POST',
      body: JSON.stringify(projectData)
    });
    
    return data.project;
  } catch (error) {
    console.error('Error creating project:', error);
    throw error;
  }
};

/**
 * Update a project
 * 
 * @param {number|string} projectId - ID of the project
 * @param {Object} projectData - Updated project data
 * @returns {Promise<Object>} - Updated project
 */
export const updateProject = async (projectId, projectData) => {
  try {
    const data = await authFetch(`/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(projectData)
    });
    
    return data.project;
  } catch (error) {
    console.error(`Error updating project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Delete a project
 * 
 * @param {number|string} projectId - ID of the project to delete
 * @returns {Promise<Object>} - Deletion response
 */
export const deleteProject = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}`, {
      method: 'DELETE'
    });
    
    return data;
  } catch (error) {
    console.error(`Error deleting project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Upload citation file to a project
 * 
 * @param {number|string} projectId - ID of the project
 * @param {File} file - Citation file (CSV or Excel)
 * @returns {Promise<Object>} - Upload response
 */
export const uploadCitationFile = async (projectId, file) => {
  try {
    const token = getToken();
    
    if (!token) {
      throw new Error('Authentication required');
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/citations/projects/${projectId}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || 'File upload failed');
    }
    
    return data;
  } catch (error) {
    console.error(`Error uploading file to project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Update project keywords
 * 
 * @param {number|string} projectId - ID of the project
 * @param {Object} keywords - Keywords to update
 * @param {Array<string>} keywords.include_keywords - Keywords that indicate relevance
 * @param {Array<string>} keywords.exclude_keywords - Keywords that indicate irrelevance
 * @returns {Promise<Object>} - Update response
 */
export const updateProjectKeywords = async (projectId, keywords) => {
  try {
    const data = await authFetch(`/projects/${projectId}/update-keywords`, {
      method: 'POST',
      body: JSON.stringify(keywords)
    });
    
    return data;
  } catch (error) {
    console.error(`Error updating keywords for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Get project summary
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Object>} - Project summary
 */
export const getProjectSummary = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}/summary`);
    return data;
  } catch (error) {
    console.error(`Error getting summary for project ${projectId}:`, error);
    throw error;
  }
};

/**
 * Complete a project
 * 
 * @param {number|string} projectId - ID of the project
 * @returns {Promise<Object>} - Completion response
 */
export const completeProject = async (projectId) => {
  try {
    const data = await authFetch(`/projects/${projectId}/complete`, {
      method: 'POST'
    });
    
    return data;
  } catch (error) {
    console.error(`Error completing project ${projectId}:`, error);
    throw error;
  }
};

export default {
    createProject,
    getProjects,
    getProject,
    createProject,
    updateProject,
    deleteProject,
    uploadCitationFile,
    updateProjectKeywords,
    getProjectSummary,
    completeProject
  };
