import React from 'react';

const CitationCard = ({ citation, onSelect, isSelectedRelevant, isSelectedIrrelevant }) => {
  // Determine if this citation can be selected (either not selected or already in correct category)
  const canSelectRelevant = !isSelectedIrrelevant;
  const canSelectIrrelevant = !isSelectedRelevant;

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden border border-gray-200">
      <div className="p-4">
        <h3 className="font-medium text-gray-900">{citation.title}</h3>
        
        {citation.abstract && (
          <div className="mt-2">
            <p className="text-sm text-gray-600 line-clamp-3">{citation.abstract}</p>
            {citation.abstract.length > 300 && (
              <button 
                className="text-xs text-blue-600 mt-1 hover:underline"
                onClick={() => alert(citation.abstract)}
              >
                Read more
              </button>
            )}
          </div>
        )}
        
        <div className="mt-4 flex space-x-2">
          <button
            onClick={() => canSelectRelevant && onSelect(citation, true)}
            className={`px-3 py-1 rounded text-sm ${
              isSelectedRelevant
                ? 'bg-green-100 text-green-800 border border-green-300'
                : canSelectRelevant
                ? 'bg-gray-100 text-gray-800 border border-gray-300 hover:bg-gray-200'
                : 'bg-gray-100 text-gray-400 border border-gray-300 cursor-not-allowed'
            }`}
            disabled={!canSelectRelevant}
          >
            Relevant
          </button>
          
          <button
            onClick={() => canSelectIrrelevant && onSelect(citation, false)}
            className={`px-3 py-1 rounded text-sm ${
              isSelectedIrrelevant
                ? 'bg-red-100 text-red-800 border border-red-300'
                : canSelectIrrelevant
                ? 'bg-gray-100 text-gray-800 border border-gray-300 hover:bg-gray-200'
                : 'bg-gray-100 text-gray-400 border border-gray-300 cursor-not-allowed'
            }`}
            disabled={!canSelectIrrelevant}
          >
            Irrelevant
          </button>
        </div>
      </div>
    </div>
  );
};

export default CitationCard;