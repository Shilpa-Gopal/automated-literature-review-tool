import React from 'react';
import { Link } from 'react-router-dom';

const ProjectCard = ({ project }) => {
  const statusClass = {
    created: 'bg-blue-100 text-blue-800',
    inProgress: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800'
  };

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="p-5">
        <h3 className="text-lg font-medium text-gray-900">{project.name}</h3>
        <div className="mt-2 flex items-center text-sm text-gray-500">
          <span>Created: {new Date(project.createdAt).toLocaleDateString()}</span>
        </div>
        <div className="mt-2">
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusClass[project.status]}`}>
            {project.status}
          </span>
        </div>
        <div className="mt-2 text-sm">
          <span>{project.citationCount || 0} citations</span>
        </div>
        <div className="mt-4">
          <Link
            to={`/project/${project.id}`}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            View Project
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ProjectCard;