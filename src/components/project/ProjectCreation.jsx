import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { processFile } from '../../utils/fileHandlers';
import projectService from '../../services/projects';
console.log("Project service:", projectService);

const ProjectCreation = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [file, setFile] = useState(null);
  const [fileData, setFileData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setLoading(true);
    setError('');

    try {
      const data = await processFile(selectedFile);
      setFileData(data);
    } catch (err) {
      setError(`Error processing file: ${err.message}`);
      setFile(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    console.log("Creating project with:", projectService.createProject);
    e.preventDefault();
    if (!name.trim() || !fileData) return;

    setLoading(true);
    try {
      const newProject = await projectService.createProject({
        name,
        data: fileData,
        citationCount: fileData.length
      });
      navigate(`/project/${newProject.id}`);
    } catch (err) {
      setError(`Error creating project: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-6">Create New Project</h2>
      
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Project Name
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Upload Dataset
          </label>
          <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
            <div className="space-y-1 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4h-12a4 4 0 01-4-4v-4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="flex text-sm text-gray-600">
                <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                  <span>Upload a file</span>
                  <input 
                    id="file-upload" 
                    name="file-upload" 
                    type="file"
                    accept=".csv,.xlsx,.xls" 
                    className="sr-only"
                    onChange={handleFileChange}
                    required
                  />
                </label>
                <p className="pl-1">or drag and drop</p>
              </div>
              <p className="text-xs text-gray-500">CSV or Excel files only</p>
            </div>
          </div>
        </div>
        
        {loading && (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Processing file...</p>
          </div>
        )}
        
        {fileData && (
          <div className="bg-gray-50 p-4 rounded">
            <h3 className="text-sm font-medium text-gray-700">File Preview</h3>
            <p className="text-sm text-gray-500 mt-1">
              {fileData.length} citations loaded
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Fields: {Object.keys(fileData[0] || {}).join(', ')}
            </p>
          </div>
        )}
        
        <button
          type="submit"
          disabled={!name.trim() || !fileData || loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          Create Project
        </button>
      </form>
    </div>
  );
};

export default ProjectCreation;