from flask import Blueprint, request, jsonify
import os
from datetime import datetime

from ..models.user import User
from ..models.project import Project
from ..models.citation import Citation,TrainingSelection
from ..api.auth import token_required
from ..services.project_service import ProjectService

projects_api = Blueprint('projects_api', __name__)
project_service = ProjectService()

@projects_api.route('/', methods=['GET'])
@token_required
def get_projects(current_user):
    """Get all projects for the current user."""
    projects = Project.query.filter_by(user_id=current_user.id).all()
    
    # Format projects
    formatted_projects = []
    for project in projects:
        # Count citations
        citation_count = Citation.query.filter_by(project_id=project.id).count()
        
        formatted_projects.append({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'status': project.status,
            'citationCount': citation_count,
            'currentIteration': project.current_iteration,
            'createdAt': project.created_at.isoformat() if project.created_at else None,
            'updatedAt': project.updated_at.isoformat() if project.updated_at else None
        })
    
    return jsonify({
        'success': True,
        'projects': formatted_projects
    })

@projects_api.route('/', methods=['POST'])
@token_required
def create_project(current_user):
    """Create a new project."""
    # Get request data
    data = request.json
    
    # Validate required fields
    if 'name' not in data or not data['name']:
        return jsonify({'success': False, 'message': 'Project name is required'}), 400
    
    # Extract data
    name = data['name'].strip()
    description = data.get('description', '').strip()
    
    # Create project
    new_project = Project(
        name=name,
        description=description,
        status='created',
        user_id=current_user.id
    )
    
    try:
        # Add project to database
        db.session.add(new_project)
        db.session.commit()
        
        # Create project directories
        project_dir = os.path.join('uploads', str(current_user.id), str(new_project.id))
        os.makedirs(project_dir, exist_ok=True)
        
        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'project': {
                'id': new_project.id,
                'name': new_project.name,
                'description': new_project.description,
                'status': new_project.status,
                'createdAt': new_project.created_at.isoformat() if new_project.created_at else None
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Project creation failed: {str(e)}'}), 500

@projects_api.route('/<int:project_id>', methods=['GET'])
@token_required
def get_project(current_user, project_id):
    """Get a specific project."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Count citations
    citation_count = Citation.query.filter_by(project_id=project.id).count()
    
    # Format project details
    project_details = {
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'status': project.status,
        'citationCount': citation_count,
        'currentIteration': project.current_iteration,
        'includeKeywords': project.include_keywords,
        'excludeKeywords': project.exclude_keywords,
        'createdAt': project.created_at.isoformat() if project.created_at else None,
        'updatedAt': project.updated_at.isoformat() if project.updated_at else None
    }
    
    return jsonify({
        'success': True,
        'project': project_details
    })

@projects_api.route('/<int:project_id>', methods=['PUT'])
@token_required
def update_project(current_user, project_id):
    """Update a project."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Get request data
    data = request.json
    
    # Update fields if provided
    if 'name' in data and data['name']:
        project.name = data['name'].strip()
    
    if 'description' in data:
        project.description = data['description'].strip()
    
    project.updated_at = datetime.utcnow()
    
    try:
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project updated successfully',
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'status': project.status,
                'updatedAt': project.updated_at.isoformat() if project.updated_at else None
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Update failed: {str(e)}'}), 500

@projects_api.route('/<int:project_id>', methods=['DELETE'])
@token_required
def delete_project(current_user, project_id):
    """Delete a project."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    try:
        # Delete project from database
        db.session.delete(project)
        db.session.commit()
        
        # Clean up project directories and files
        project_dir = os.path.join('uploads', str(current_user.id), str(project_id))
        if os.path.exists(project_dir):
            for file in os.listdir(project_dir):
                os.remove(os.path.join(project_dir, file))
            os.rmdir(project_dir)
        
        # Remove model files
        model_dir = os.path.join('models', str(project_id))
        if os.path.exists(model_dir):
            for file in os.listdir(model_dir):
                os.remove(os.path.join(model_dir, file))
            os.rmdir(model_dir)
        
        return jsonify({
            'success': True,
            'message': 'Project deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Deletion failed: {str(e)}'}), 500

@projects_api.route('/<int:project_id>/summary', methods=['GET'])
@token_required
def get_project_summary(current_user, project_id):
    """Get a summary of the project status and statistics."""
    # Use project service to get summary
    result = project_service.get_project_summary(project_id, current_user.id)
    
    if not result['success']:
        return jsonify(result), 404
    
    return jsonify(result)