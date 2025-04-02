import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/shared/Layout';
import ProjectList from '../components/project/ProjectList';
import Loading from '../components/shared/Loading';
import { useAuth } from '../contexts/AuthContext';

const Dashboard = () => {
  const { currentUser } = useAuth();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // This would be replaced with a real API call in a production app
        const response = await fetch(`${process.env.REACT_APP_API_URL || '/api'}/projects`);
        
        // If the API is not yet implemented, use mock data
        if (!response.ok) {
          throw new Error("API endpoint not available");
        }
        
        const data = await response.json();
        setProjects(data);
      } catch (error) {
        console.log("Using mock data due to API error:", error.message);
        
        // Mock data for development
        const mockProjects = [
          {
            id: '1',
            name: 'Cancer Biomarkers Review',
            createdAt: new Date('2024-01-15').toISOString(),
            status: 'inProgress',
            citationCount: 234
          },
          {
            id: '2',
            name: 'HPV Treatment Efficacy',
            createdAt: new Date('2024-02-22').toISOString(),
            status: 'completed',
            citationCount: 156
          },
          {
            id: '3',
            name: 'Genomic Markers in Precision Medicine',
            createdAt: new Date('2024-03-10').toISOString(),
            status: 'created',
            citationCount: 312
          }
        ];
        
        setProjects(mockProjects);
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, []);

  return (
    <Layout>
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">My Projects</h1>
          <Link
            to="/project/new"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Create New Project
          </Link>
        </div>

        {loading ? (
          <Loading message="Loading your projects..." />
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            Error loading projects: {error}
          </div>
        ) : (
          <ProjectList projects={projects} />
        )}
      </div>
    </Layout>
  );
};

export default Dashboard;
