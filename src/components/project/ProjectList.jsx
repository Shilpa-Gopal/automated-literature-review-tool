import React from 'react';
import ProjectCard from './ProjectCard';

const ProjectList = ({ projects }) => {
  if (!projects || projects.length === 0) {
    return (
      <div className="text-center py-10">
        <h3 className="text-lg font-medium text-gray-500">No projects yet</h3>
        <p className="mt-1 text-sm text-gray-500">Create a new project to get started</p>
      </div>
    );
  }

  return (
    <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
      {projects.map(project => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
};

export default ProjectList;