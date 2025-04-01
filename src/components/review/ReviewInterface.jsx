import React, { useState, useEffect } from 'react';
import CitationCard from './CitationCard';

const ReviewInterface = ({ citations, keywords, onTrainingComplete, onDownloadResults }) => {
  const [selectedRelevant, setSelectedRelevant] = useState([]);
  const [selectedIrrelevant, setSelectedIrrelevant] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [isTraining, setIsTraining] = useState(false);
  const [iteration, setIteration] = useState(1);
  const [sortedCitations, setSortedCitations] = useState([]);
  const [trainingHistory, setTrainingHistory] = useState([]);
  
  const citationsPerPage = 5;
  const maxIterations = 10;
  
  useEffect(() => {
    // Initialize with unsorted citations
    setSortedCitations([...citations].map((citation, index) => ({
      ...citation,
      id: citation.id || index,
      score: 0.5 // Initial neutral score
    })));
  }, [citations]);
  
  // Calculate if we have enough selected citations
  const isEnoughSelected = selectedRelevant.length >= 5 && selectedIrrelevant.length >= 5;
  
  // Get current page citations
  const indexOfLastCitation = currentPage * citationsPerPage;
  const indexOfFirstCitation = indexOfLastCitation - citationsPerPage;
  const currentCitations = sortedCitations.slice(indexOfFirstCitation, indexOfLastCitation);
  
  const handleCitationSelect = (citation, isRelevant) => {
    if (isRelevant) {
      if (selectedRelevant.some(c => c.id === citation.id)) {
        setSelectedRelevant(selectedRelevant.filter(c => c.id !== citation.id));
      } else if (selectedRelevant.length < 5) {
        setSelectedRelevant([...selectedRelevant, citation]);
      }
    } else {
      if (selectedIrrelevant.some(c => c.id === citation.id)) {
        setSelectedIrrelevant(selectedIrrelevant.filter(c => c.id !== citation.id));
      } else if (selectedIrrelevant.length < 5) {
        setSelectedIrrelevant([...selectedIrrelevant, citation]);
      }
    }
  };
  
  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
  };
  
  const handleTraining = () => {
    if (!isEnoughSelected) return;
    
    setIsTraining(true);
    
    // Add current selections to training history
    const newTrainingHistory = [
      ...trainingHistory,
      {
        iteration,
        relevant: selectedRelevant,
        irrelevant: selectedIrrelevant
      }
    ];
    setTrainingHistory(newTrainingHistory);
    
    // Simulate ML model training and re-scoring
    setTimeout(() => {
      // In a real app, this would call your backend ML service
      // For now, we'll simulate re-scoring based on selections
      const newSortedCitations = simulateModelTraining(sortedCitations, selectedRelevant, selectedIrrelevant);
      
      setSortedCitations(newSortedCitations);
      
      if (iteration < maxIterations) {
        setIteration(prev => prev + 1);
        // Reset selections for next iteration
        setSelectedRelevant([]);
        setSelectedIrrelevant([]);
        setCurrentPage(1);
      }
      
      setIsTraining(false);
    }, 2000);
  };
  
  // Simulate ML model training and re-scoring of citations
  const simulateModelTraining = (allCitations, relevant, irrelevant) => {
    // In a real implementation, this would be replaced with actual ML model predictions
    return allCitations.map(citation => {
      // Check if this citation was selected as relevant
      if (relevant.some(c => c.id === citation.id)) {
        return { ...citation, score: 1.0 }; // Highest relevance
      }
      
      // Check if this citation was selected as irrelevant
      if (irrelevant.some(c => c.id === citation.id)) {
        return { ...citation, score: 0.0 }; // Lowest relevance
      }
      
      // For other citations, adjust scores based on similarity to selected ones
      // This is just a simple simulation
      const currentScore = citation.score || 0.5;
      const randomAdjustment = (Math.random() * 0.2) - 0.1; // Random adjustment between -0.1 and 0.1
      const newScore = Math.max(0, Math.min(1, currentScore + randomAdjustment));
      
      return { ...citation, score: newScore };
    }).sort((a, b) => b.score - a.score); // Sort by score, highest first
  };
  
  const handleComplete = () => {
    onTrainingComplete({
      sortedCitations,
      trainingHistory,
      completedIterations: iteration
    });
  };
  
  return (
    <div className="space-y-6">
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Citation Review - Iteration {iteration}/{maxIterations}</h2>
          <div className="flex space-x-4">
            <div className="bg-green-50 text-green-700 px-3 py-1 rounded-full text-sm">
              Relevant: {selectedRelevant.length}/5
            </div>
            <div className="bg-red-50 text-red-700 px-3 py-1 rounded-full text-sm">
              Irrelevant: {selectedIrrelevant.length}/5
            </div>
          </div>
        </div>
        
        <p className="text-sm text-gray-600 mb-4">
          Select 5 relevant and 5 irrelevant citations to train the model. This will help refine the results.
          The model will learn from your selections and improve the ranking.
        </p>
        
        {isTraining ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-sm text-gray-600">Training model and re-ranking citations...</p>
          </div>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {currentCitations.map(citation => (
                <CitationCard
                  key={citation.id}
                  citation={citation}
                  onSelect={handleCitationSelect}
                  isSelectedRelevant={selectedRelevant.some(c => c.id === citation.id)}
                  isSelectedIrrelevant={selectedIrrelevant.some(c => c.id === citation.id)}
                />
              ))}
              
              {currentCitations.length === 0 && (
                <div className="text-center py-6 text-gray-500">
                  No citations available on this page.
                </div>
              )}
            </div>
            
            <div className="flex justify-between items-center">
              <div className="flex space-x-2">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-3 py-1 rounded border text-sm disabled:text-gray-400"
                >
                  Previous
                </button>
                <span className="px-3 py-1 text-sm">
                  Page {currentPage} of {Math.ceil(sortedCitations.length / citationsPerPage)}
                </span>
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={indexOfLastCitation >= sortedCitations.length}
                  className="px-3 py-1 rounded border text-sm disabled:text-gray-400"
                >
                  Next
                </button>
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={handleTraining}
                  disabled={!isEnoughSelected}
                  className="px-4 py-2 bg-blue-600 text-white rounded disabled:bg-blue-300"
                >
                  {iteration < maxIterations ? 'Train Model & Continue' : 'Final Training'}
                </button>
                
                {iteration > 1 && (
                  <button
                    onClick={handleComplete}
                    className="px-4 py-2 bg-green-600 text-white rounded"
                  >
                    Complete & Download Results
                  </button>
                )}
              </div>
            </div>
          </>
        )}
      </div>
      
      {iteration > 1 && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="font-medium mb-2">Training Progress</h3>
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-blue-600 rounded-full"
              style={{ width: `${(iteration / maxIterations) * 100}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            {iteration < maxIterations 
              ? `${iteration} of ${maxIterations} iterations completed` 
              : 'Training complete!'}
          </p>
        </div>
      )}
    </div>
  );
};

export default ReviewInterface;