import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/shared/Layout';
import Loading from '../components/shared/Loading';
import ProjectCreation from '../components/project/ProjectCreation';
import KeywordSelection from '../components/review/KeywordSelection';
import ReviewInterface from '../components/review/ReviewInterface';

const ProjectView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState('loading');
  const [citations, setCitations] = useState([]);
  const [keywords, setKeywords] = useState({ includeKeywords: [], excludeKeywords: [] });
  const [processedResults, setProcessedResults] = useState(null);

  useEffect(() => {
    const fetchProject = async () => {
      if (id === 'new') {
        setCurrentStep('create');
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      
      try {
        // This would be replaced with a real API call in a production app
        // Example: const response = await fetch(`/api/projects/${id}`);
        
        // For now, simulate API call with timeout
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Mock data for development
        const mockProject = {
          id,
          name: `Project ${id}`,
          createdAt: new Date().toISOString(),
          status: id === '1' ? 'inProgress' : (id === '2' ? 'completed' : 'created'),
          citationCount: 150 + (parseInt(id) * 40),
          keywords: {
            includeKeywords: ['cancer', 'biomarker', 'clinical trial'],
            excludeKeywords: ['animal study', 'in vitro']
          }
        };
        
        // Generate mock citations
        const mockCitations = Array.from({ length: mockProject.citationCount }, (_, i) => ({
          id: `cit-${i}`,
          title: `Citation ${i+1}: ${['Effects of biomarker X on cancer progression', 
                                      'Clinical evaluation of targeted therapy', 
                                      'Genomic analysis of tumor samples', 
                                      'Patient outcomes in randomized trials'][i % 4]}`,
          abstract: `This study ${['investigates', 'examines', 'analyzes', 'reports on'][i % 4]} the ${['effects', 'impact', 'relationship', 'correlation'][i % 4]} of ${['biomarkers', 'treatment methods', 'genetic factors', 'clinical interventions'][i % 4]} on ${['cancer progression', 'patient outcomes', 'disease recurrence', 'survival rates'][i % 4]}. The research ${['was conducted', 'took place', 'was performed', 'occurred'][i % 4]} using data from ${['clinical trials', 'patient cohorts', 'hospital records', 'multi-center studies'][i % 4]}.`,
          authors: `Author ${String.fromCharCode(65 + (i % 26))}, Author ${String.fromCharCode(66 + (i % 25))}, Author ${String.fromCharCode(67 + (i % 24))}`,
          year: 2018 + (i % 7),
          journal: `Journal of ${['Medical Research', 'Clinical Oncology', 'Cancer Studies', 'Biomedical Science'][i % 4]}`,
          pmid: `10${i.toString().padStart(5, '0')}`
        }));
        
        setProject(mockProject);
        setCitations(mockCitations);
        setKeywords(mockProject.keywords);
        
        // Determine current step based on project status
        if (mockProject.status === 'created') {
          setCurrentStep('keywords');
        } else if (mockProject.status === 'inProgress') {
          setCurrentStep('review');
        } else {
          setCurrentStep('completed');
          
          // Mock processed results for completed projects
          setProcessedResults({
            sortedCitations: mockCitations.map(citation => ({
              ...citation,
              score: Math.random().toFixed(2)
            })).sort((a, b) => b.score - a.score),
            trainingHistory: Array.from({ length: 5 }, (_, i) => ({
              iteration: i + 1,
              relevant: mockCitations.slice(0, 5),
              irrelevant: mockCitations.slice(mockCitations.length - 5)
            })),
            completedIterations: 5
          });
        }
      } catch (error) {
        console.error('Error fetching project:', error);
        setError('Failed to load project data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchProject();
  }, [id]);

  const handleProjectCreated = (newProject) => {
    setProject(newProject);
    setCitations(newProject.citations || []);
    setCurrentStep('keywords');
  };

  const handleKeywordSelectionComplete = (selectedKeywords) => {
    setKeywords(selectedKeywords);
    setCurrentStep('review');
    
    // In a real app, you would save these keywords to your backend
    console.log('Selected keywords:', selectedKeywords);
  };

  const handleTrainingComplete = (results) => {
    setProcessedResults(results);
    setCurrentStep('completed');
    
    // In a real app, you would save these results to your backend
    console.log('Training completed with results:', results);
  };

  const handleDownloadResults = () => {
    if (!processedResults) return;
    
    // Create CSV content from the sorted citations
    const csvContent = processedResults.sortedCitations.map(citation => {
      return `"${citation.id}","${citation.title.replace(/"/g, '""')}","${citation.score}","${citation.score >= 0.5 ? 'Relevant' : 'Irrelevant'}"`;
    }).join('\n');
    
    const header = 'ID,Title,Relevance Score,Classification\n';
    const blob = new Blob([header + csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    // Create a link and trigger download
    const a = document.createElement('a');
    a.href = url;
    a.download = `literature-review-results-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Layout>
        <Loading message="Loading project data..." />
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
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-semibold text-gray-900">
              {id === 'new' ? 'Create New Project' : project?.name}
            </h1>
            
            {currentStep === 'completed' && (
              <button
                onClick={handleDownloadResults}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                Download Results
              </button>
            )}
          </div>
          
          {currentStep !== 'create' && (
            <div className="mt-2 flex items-center space-x-2">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                currentStep === 'keywords' ? 'bg-blue-100 text-blue-800' :
                currentStep === 'review' ? 'bg-yellow-100 text-yellow-800' :
                'bg-green-100 text-green-800'
              }`}>
                {currentStep === 'keywords' ? 'Keyword Selection' :
                 currentStep === 'review' ? 'Citation Review' :
                 'Analysis Complete'}
              </span>
              {project?.citationCount && (
                <span className="text-sm text-gray-500">
                  {project.citationCount} citations
                </span>
              )}
            </div>
          )}
        </div>

        {currentStep === 'create' && (
          <ProjectCreation onProjectCreated={handleProjectCreated} />
        )}

        {currentStep === 'keywords' && (
          <KeywordSelection 
            citations={citations}
            onComplete={handleKeywordSelectionComplete}
          />
        )}

        {currentStep === 'review' && (
          <ReviewInterface
            citations={citations}
            keywords={keywords}
            onTrainingComplete={handleTrainingComplete}
          />
        )}

        {currentStep === 'completed' && processedResults && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium mb-4">Analysis Results</h2>
            
            <div className="mb-6">
              <h3 className="font-medium mb-2">Statistics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-500">Total Citations</p>
                  <p className="text-xl font-semibold">{processedResults.sortedCitations.length}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-500">Iterations Completed</p>
                  <p className="text-xl font-semibold">{processedResults.completedIterations}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-500">Relevant Citations</p>
                  <p className="text-xl font-semibold">{processedResults.sortedCitations.filter(c => c.score >= 0.5).length}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm text-gray-500">Irrelevant Citations</p>
                  <p className="text-xl font-semibold">{processedResults.sortedCitations.filter(c => c.score < 0.5).length}</p>
                </div>
              </div>
            </div>
            
            <div className="mb-6">
              <h3 className="font-medium mb-2">Top Relevant Citations</h3>
              <div className="space-y-3">
                {processedResults.sortedCitations.slice(0, 5).map(citation => (
                  <div key={citation.id} className="border rounded p-3">
                    <div className="flex justify-between">
                      <h4 className="font-medium">{citation.title}</h4>
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        Score: {citation.score}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{citation.authors} ({citation.year})</p>
                  </div>
                ))}
              </div>
            </div>
            
            <button
              onClick={handleDownloadResults}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Download Complete Results
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default ProjectView;
