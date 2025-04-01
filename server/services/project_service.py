import logging
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from ..models.user import User
from ..models.project import Project
from ..models.citation import Citation,TrainingSelection
from ..services.citation_service import CitationService

class ProjectService:
    """Service for managing projects and project-related operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.citation_service = CitationService()
    
    def create_project(self, user_id: int, name: str, description: str = "") -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new project.
        
        Args:
            user_id: ID of the user
            name: Project name
            description: Project description (optional)
            
        Returns:
            Tuple of (success, message, project_dict)
        """
        try:
            # Validate name
            if not name or not name.strip():
                return False, "Project name is required", None
            
            # Create project
            project = Project(
                user_id=user_id,
                name=name.strip(),
                description=description.strip() if description else "",
                status="created"
            )
            
            # Add to database
            db.session.add(project)
            db.session.commit()
            
            # Create project directories
            os.makedirs(os.path.join('uploads', str(user_id), str(project.id)), exist_ok=True)
            os.makedirs(os.path.join('models', str(project.id)), exist_ok=True)
            os.makedirs(os.path.join('exports', str(project.id)), exist_ok=True)
            
            # Return project details
            project_dict = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'createdAt': project.created_at.isoformat() if project.created_at else None
            }
            
            return True, "Project created successfully", project_dict
            
        except Exception as e:
            self.logger.error(f"Error creating project: {str(e)}")
            db.session.rollback()
            return False, f"Error creating project: {str(e)}", None
    
    def get_project(self, project_id: int, user_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get a project by ID.
        
        Args:
            project_id: ID of the project
            user_id: ID of the user (for access control)
            
        Returns:
            Tuple of (success, message, project_dict)
        """
        try:
            # Get project
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return False, "Project not found or access denied", None
            
            # Get citation count
            citation_count = Citation.query.filter_by(project_id=project_id).count()
            
            # Format project details
            project_dict = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'currentIteration': project.current_iteration,
                'includeKeywords': project.include_keywords,
                'excludeKeywords': project.exclude_keywords,
                'citationCount': citation_count,
                'createdAt': project.created_at.isoformat() if project.created_at else None,
                'updatedAt': project.updated_at.isoformat() if project.updated_at else None
            }
            
            return True, "Project retrieved successfully", project_dict
            
        except Exception as e:
            self.logger.error(f"Error getting project: {str(e)}")
            return False, f"Error getting project: {str(e)}", None
    
    def get_user_projects(self, user_id: int) -> List[Dict]:
        """
        Get all projects for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of project dictionaries
        """
        try:
            # Get projects
            projects = Project.query.filter_by(user_id=user_id).all()
            
            # Format projects
            project_list = []
            for project in projects:
                # Get citation count
                citation_count = Citation.query.filter_by(project_id=project.id).count()
                
                project_dict = {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'status': project.status,
                    'currentIteration': project.current_iteration,
                    'citationCount': citation_count,
                    'createdAt': project.created_at.isoformat() if project.created_at else None,
                    'updatedAt': project.updated_at.isoformat() if project.updated_at else None
                }
                
                project_list.append(project_dict)
            
            return project_list
            
        except Exception as e:
            self.logger.error(f"Error getting user projects: {str(e)}")
            return []
    
    def update_project(self, project_id: int, user_id: int, name: str = None, 
                      description: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Update a project.
        
        Args:
            project_id: ID of the project
            user_id: ID of the user (for access control)
            name: New project name (optional)
            description: New project description (optional)
            
        Returns:
            Tuple of (success, message, project_dict)
        """
        try:
            # Get project
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return False, "Project not found or access denied", None
            
            # Update fields if provided
            if name is not None:
                project.name = name.strip()
            
            if description is not None:
                project.description = description.strip()
            
            # Update timestamp
            project.updated_at = datetime.utcnow()
            
            # Save changes
            db.session.commit()
            
            # Format project details
            project_dict = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'updatedAt': project.updated_at.isoformat() if project.updated_at else None
            }
            
            return True, "Project updated successfully", project_dict
            
        except Exception as e:
            self.logger.error(f"Error updating project: {str(e)}")
            db.session.rollback()
            return False, f"Error updating project: {str(e)}", None
    
    def delete_project(self, project_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a project.
        
        Args:
            project_id: ID of the project
            user_id: ID of the user (for access control)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get project
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return False, "Project not found or access denied"
            
            # Delete project
            db.session.delete(project)
            db.session.commit()
            
            # Clean up project directories
            project_upload_dir = os.path.join('uploads', str(user_id), str(project_id))
            if os.path.exists(project_upload_dir):
                for file in os.listdir(project_upload_dir):
                    os.remove(os.path.join(project_upload_dir, file))
                os.rmdir(project_upload_dir)
            
            model_dir = os.path.join('models', str(project_id))
            if os.path.exists(model_dir):
                for file in os.listdir(model_dir):
                    os.remove(os.path.join(model_dir, file))
                os.rmdir(model_dir)
            
            export_dir = os.path.join('exports', str(project_id))
            if os.path.exists(export_dir):
                for file in os.listdir(export_dir):
                    os.remove(os.path.join(export_dir, file))
                os.rmdir(export_dir)
            
            return True, "Project deleted successfully"
            
        except Exception as e:
            self.logger.error(f"Error deleting project: {str(e)}")
            db.session.rollback()
            return False, f"Error deleting project: {str(e)}"
    
    def update_project_keywords(self, project_id: int, user_id: int, 
                              include_keywords: List[str], exclude_keywords: List[str]) -> Tuple[bool, str]:
        """
        Update a project's keywords.
        
        Args:
            project_id: ID of the project
            user_id: ID of the user (for access control)
            include_keywords: List of keywords to include
            exclude_keywords: List of keywords to exclude
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get project
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return False, "Project not found or access denied"
            
            # Update keywords
            project.include_keywords = include_keywords
            project.exclude_keywords = exclude_keywords
            
            # Update timestamp
            project.updated_at = datetime.utcnow()
            
            # Save changes
            db.session.commit()
            
            return True, "Project keywords updated successfully"
            
        except Exception as e:
            self.logger.error(f"Error updating project keywords: {str(e)}")
            db.session.rollback()
            return False, f"Error updating project keywords: {str(e)}"
    
    def get_project_summary(self, project_id: int, user_id: int) -> Dict:
        """
        Get a summary of a project's status.
        
        Args:
            project_id: ID of the project
            user_id: ID of the user (for access control)
            
        Returns:
            Dictionary with project summary
        """
        try:
            # Get project
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return {'success': False, 'message': "Project not found or access denied"}
            
            # Get citation stats
            citation_stats = self.citation_service.get_citation_stats(project_id)
            
            # Get training iterations
            iterations = TrainingIteration.query.filter_by(project_id=project_id) \
                .order_by(TrainingIteration.iteration_number).all()
            
            # Format iterations
            iteration_data = []
            for iteration in iterations:
                # Count selections
                relevant_count = TrainingSelection.query.filter_by(
                    iteration_id=iteration.id, is_relevant=True
                ).count()
                
                irrelevant_count = TrainingSelection.query.filter_by(
                    iteration_id=iteration.id, is_relevant=False
                ).count()
                
                iteration_data.append({
                    'iteration_number': iteration.iteration_number,
                    'relevant_count': relevant_count,
                    'irrelevant_count': irrelevant_count,
                    'created_at': iteration.created_at.isoformat() if iteration.created_at else None
                })
            
            # Format project details
            project_dict = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'currentIteration': project.current_iteration,
                'includeKeywords': project.include_keywords,
                'excludeKeywords': project.exclude_keywords,
                'createdAt': project.created_at.isoformat() if project.created_at else None,
                'updatedAt': project.updated_at.isoformat() if project.updated_at else None
            }
            
            return {
                'success': True,
                'project': project_dict,
                'citation_stats': citation_stats,
                'iterations': iteration_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting project summary: {str(e)}")
            return {'success': False, 'message': f"Error getting project summary: {str(e)}"}
    
    def complete_project(self, project_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Mark a project as completed.
        
        Args:
            project_id: ID of the project
            user_id: ID of the user (for access control)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get project
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return False, "Project not found or access denied"
            
            # Update status
            project.status = "completed"
            project.updated_at = datetime.utcnow()
            
            # Save changes
            db.session.commit()
            
            return True, "Project marked as completed"
            
        except Exception as e:
            self.logger.error(f"Error completing project: {str(e)}")
            db.session.rollback()
            return False, f"Error completing project: {str(e)}"