import React, { useState, useEffect } from 'react';

const KeywordSelection = ({ citations, onComplete }) => {
  const [generatedKeywords, setGeneratedKeywords] = useState([]);
  const [includedKeywords, setIncludedKeywords] = useState([]);
  const [excludedKeywords, setExcludedKeywords] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [customKeyword, setCustomKeyword] = useState('');

  useEffect(() => {
    generateKeywords();
  }, [citations]);

  const generateKeywords = () => {
    setIsGenerating(true);
    
    // This would be replaced with actual keyword extraction
    // Using text analysis on the citations' titles and abstracts
    setTimeout(() => {
      // Extract common terms from citations
      const extractedKeywords = extractKeywordsFromCitations(citations);
      setGeneratedKeywords(extractedKeywords);
      setIsGenerating(false);
    }, 1500);
  };

  // Function to simulate extracting keywords from citations
  const extractKeywordsFromCitations = (citations) => {
    // In a real implementation, this would use TF-IDF or other NLP techniques
    // to extract meaningful keywords from the citation text
    const commonKeywordsInBiomedicalResearch = [
      'cancer', 'clinical trial', 'biomarker', 'ctDNA', 'treatment',
      'therapy', 'mutation', 'genomic', 'survival', 'recurrence',
      'metastasis', 'biopsy', 'screening', 'detection', 'diagnosis',
      'prognosis', 'therapeutic', 'immunotherapy', 'chemotherapy', 'radiotherapy'
    ];
    
    return commonKeywordsInBiomedicalResearch;
  };

  const toggleInclude = (keyword) => {
    if (includedKeywords.includes(keyword)) {
      setIncludedKeywords(includedKeywords.filter(k => k !== keyword));
    } else {
      setIncludedKeywords([...includedKeywords, keyword]);
      setExcludedKeywords(excludedKeywords.filter(k => k !== keyword));
    }
  };

  const toggleExclude = (keyword) => {
    if (excludedKeywords.includes(keyword)) {
      setExcludedKeywords(excludedKeywords.filter(k => k !== keyword));
    } else {
      setExcludedKeywords([...excludedKeywords, keyword]);
      setIncludedKeywords(includedKeywords.filter(k => k !== keyword));
    }
  };

  const addCustomKeyword = () => {
    if (customKeyword.trim() && !generatedKeywords.includes(customKeyword.trim())) {
      const newKeyword = customKeyword.trim();
      setGeneratedKeywords([...generatedKeywords, newKeyword]);
      setCustomKeyword('');
      // Automatically add it to included keywords
      toggleInclude(newKeyword);
    }
  };

  const handleComplete = () => {
    if (includedKeywords.length > 0) {
      onComplete({
        includeKeywords: includedKeywords,
        excludeKeywords: excludedKeywords
      });
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Select Keywords</h2>
      <p className="text-sm text-gray-600 mb-6">
        Select keywords to include or exclude for your systematic review.
        These keywords will help train the ML model to identify relevant citations.
      </p>
      
      {isGenerating ? (
        <div className="text-center py-6">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-3 text-sm text-gray-600">Analyzing citations and generating keywords...</p>
        </div>
      ) : (
        <>
          <div className="flex space-x-2 mb-6">
            <div className="border rounded p-2 flex-1">
              <h3 className="font-medium text-sm mb-2 text-green-700">Include Keywords</h3>
              <div className="flex flex-wrap gap-2">
                {includedKeywords.map(keyword => (
                  <span 
                    key={keyword}
                    className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm flex items-center"
                  >
                    {keyword}
                    <button 
                      onClick={() => toggleInclude(keyword)}
                      className="ml-1 text-green-600 hover:text-green-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
                {includedKeywords.length === 0 && (
                  <span className="text-sm text-gray-500 italic">No keywords selected</span>
                )}
              </div>
            </div>
            
            <div className="border rounded p-2 flex-1">
              <h3 className="font-medium text-sm mb-2 text-red-700">Exclude Keywords</h3>
              <div className="flex flex-wrap gap-2">
                {excludedKeywords.map(keyword => (
                  <span 
                    key={keyword}
                    className="bg-red-100 text-red-800 px-2 py-1 rounded text-sm flex items-center"
                  >
                    {keyword}
                    <button 
                      onClick={() => toggleExclude(keyword)}
                      className="ml-1 text-red-600 hover:text-red-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
                {excludedKeywords.length === 0 && (
                  <span className="text-sm text-gray-500 italic">No keywords selected</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="mb-6">
            <div className="flex items-center mb-2">
              <input
                type="text"
                value={customKeyword}
                onChange={(e) => setCustomKeyword(e.target.value)}
                placeholder="Add custom keyword"
                className="border rounded px-3 py-1 text-sm flex-1"
                onKeyPress={(e) => e.key === 'Enter' && addCustomKeyword()}
              />
              <button
                onClick={addCustomKeyword}
                disabled={!customKeyword.trim()}
                className="ml-2 px-3 py-1 bg-blue-600 text-white rounded text-sm disabled:bg-blue-300"
              >
                Add
              </button>
            </div>
          </div>
          
          <div className="border rounded p-4">
            <h3 className="font-medium mb-3">Generated Keywords</h3>
            <div className="flex flex-wrap gap-2">
              {generatedKeywords.map(keyword => (
                <div key={keyword} className="inline-flex rounded border">
                  <span className="px-2 py-1 text-sm">{keyword}</span>
                  <button 
                    onClick={() => toggleInclude(keyword)}
                    className={`px-2 py-1 text-sm border-l ${
                      includedKeywords.includes(keyword)
                        ? 'bg-green-100 text-green-800'
                        : 'hover:bg-green-50 text-gray-600'
                    }`}
                    title="Include"
                  >
                    +
                  </button>
                  <button 
                    onClick={() => toggleExclude(keyword)}
                    className={`px-2 py-1 text-sm border-l ${
                      excludedKeywords.includes(keyword)
                        ? 'bg-red-100 text-red-800'
                        : 'hover:bg-red-50 text-gray-600'
                    }`}
                    title="Exclude"
                  >
                    -
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          <div className="mt-6">
            <button
              onClick={handleComplete}
              disabled={includedKeywords.length === 0}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Continue to Citation Review
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default KeywordSelection;