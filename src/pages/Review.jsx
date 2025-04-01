import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/shared/Layout';
import Loading from '../components/shared/Loading';
import ReviewInterface from '../components/review/ReviewInterface';

const Review = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [citations, setCitations] = useState([]);
  const [keywords, setKeywords] = useState({ includeKeywords: [], excludeKeywords: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // In a real app, fetch from API
        // const response = await fetch(`/api/projects/${projectId}`);
        // const data = await response.json();
        
        // Mock data for development
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const mockProject = {
          id: projectId,
          name: `Project ${projectId}`,
          status: 'inProgress',
          citationCount: 120,
          keywords: {
            includeKeywords: ['cancer', 'biomarker', 'clinical trial'],
            excludeKeywords: ['animal study', 'in vitro']
          }
        };
        
        const mockCitations = Array.from({ length: 120 }, (_, i) => ({
          id: `cit-${i}`,
          title: `Citation ${i+1}: Research on cancer biomarkers`,
          abstract: `This study examines various aspects of cancer biomarkers and their clinical applications.`,
          authors: `Author A, Author B, Author C`,
          year: 2020 + (i % 5),
          journal: `Journal of Medical Research`,
          pmid: `12345${i}`
        }));
        
        setProject(mockProject);
        setCitations(mockCitations);
        setKeywords(mockProject.keywords);
      } catch (err) {
        console.error('Error fetching review data:', err);
        setError('Failed to load project data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [projectId]);

  const handleTrainingComplete = (results) => {
    // In a real app, save results to backend
    console.log('Training completed with results:', results);
    
    // Navigate to project page with results
    navigate(`/project/${projectId}`);
  };

  if (loading) {
    return (
      <Layout>
        <Loading message="Loading citation data..." />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">
            Review Citations: {project?.name}
          </h1>
          <div className="mt-2 flex items-center space-x-2">
            <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium">
              Citation Review
            </span>
            {project?.citationCount && (
              <span className="text-sm text-gray-500">
                {project.citationCount} citations
              </span>
            )}
          </div>
        </div>

        <ReviewInterface
          citations={citations}
          keywords={keywords}
          onTrainingComplete={handleTrainingComplete}
        />
      </div>
    </Layout>
  );
};

export default Review;