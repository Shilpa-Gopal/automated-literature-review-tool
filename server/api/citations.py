from flask import Blueprint, request, jsonify, send_file
import os
from werkzeug.utils import secure_filename
import pandas as pd

from ..services.ml_service import MLService
from ..models.user import User
from ..models.project import Project
from ..models.citation import Citation,TrainingSelection
from ..api.auth import token_required

citations_api = Blueprint('citations_api', __name__)
ml_service = MLService()

@citations_api.route('/projects/<int:project_id>/upload', methods=['POST'])
@token_required
def upload_citations(current_user, project_id):
    """Upload and process a citation dataset file."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    # Check if allowed file type
    allowed_extensions = {'csv', 'xls', 'xlsx'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'message': 'Invalid file type. Please upload CSV or Excel file'}), 400
    
    # Save the file temporarily
    filename = secure_filename(file.filename)
    upload_dir = os.path.join('uploads', str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    # Validate the dataset
    is_valid, error_message, dataframe = ml_service.validate_citation_dataset(file_path)
    
    if not is_valid:
        # Clean up the file
        os.remove(file_path)
        return jsonify({'success': False, 'message': error_message}), 400
    
    # Import the citations into the database
    success, message, citation_count = ml_service.import_citations(project_id, dataframe)
    
    # Clean up the file
    os.remove(file_path)
    
    if not success:
        return jsonify({'success': False, 'message': message}), 500
    
    return jsonify({
        'success': True,
        'message': message,
        'citation_count': citation_count
    })

@citations_api.route('/projects/<int:project_id>/extract-keywords', methods=['GET'])
@token_required
def extract_keywords(current_user, project_id):
    """Extract keywords from project citations."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Extract keywords
    include_keywords, exclude_keywords = ml_service.extract_keywords_from_citations(project_id)
    
    return jsonify({
        'success': True,
        'include_keywords': include_keywords,
        'exclude_keywords': exclude_keywords
    })

@citations_api.route('/projects/<int:project_id>/update-keywords', methods=['POST'])
@token_required
def update_keywords(current_user, project_id):
    """Update project keywords based on user selection."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Get keywords from request
    data = request.json
    include_keywords = data.get('include_keywords', [])
    exclude_keywords = data.get('exclude_keywords', [])
    
    # Update project keywords
    success = ml_service.update_project_keywords(project_id, include_keywords, exclude_keywords)
    
    if not success:
        return jsonify({'success': False, 'message': 'Failed to update keywords'}), 500
    
    return jsonify({
        'success': True,
        'message': 'Keywords updated successfully'
    })

@citations_api.route('/projects/<int:project_id>/initial-citations', methods=['GET'])
@token_required
def get_initial_citations(current_user, project_id):
    """Get initial citations for user selection."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Get initial citations
    citations = ml_service.get_citations_for_initial_selection(project_id)
    
    return jsonify({
        'success': True,
        'citations': citations
    })

@citations_api.route('/projects/<int:project_id>/train', methods=['POST'])
@token_required
def train_model(current_user, project_id):
    """Train the model with user-selected citations."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Get training data from request
    data = request.json
    relevant_ids = data.get('relevant_ids', [])
    irrelevant_ids = data.get('irrelevant_ids', [])
    
    # Get current iteration
    current_iteration = project.current_iteration or 0
    next_iteration = current_iteration + 1
    
    # Train the model
    result = ml_service.train_model_with_selected_citations(
        project_id, relevant_ids, irrelevant_ids, next_iteration
    )
    
    if not result['success']:
        return jsonify({'success': False, 'message': result.get('error', 'Training failed')}), 500
    
    return jsonify({
        'success': True,
        'message': f'Training completed for iteration {next_iteration}',
        'iteration': next_iteration,
        'top_citations': result.get('top_citations', []),
        'bottom_citations': result.get('bottom_citations', [])
    })

@citations_api.route('/projects/<int:project_id>/citations', methods=['GET'])
@token_required
def get_sorted_citations(current_user, project_id):
    """Get sorted citations based on relevance score."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Get query parameters
    sort_order = request.args.get('sort', 'desc')
    limit = request.args.get('limit')
    if limit:
        try:
            limit = int(limit)
        except ValueError:
            limit = None
    
    # Get sorted citations
    citations = ml_service.get_sorted_citations(project_id, sort_order, limit)
    
    return jsonify({
        'success': True,
        'citations': citations,
        'total': len(citations),
        'current_iteration': project.current_iteration or 0
    })

@citations_api.route('/projects/<int:project_id>/complete', methods=['POST'])
@token_required
def complete_project(current_user, project_id):
    """Mark a project as completed."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Complete the project
    result = ml_service.complete_project(project_id)
    
    if not result['success']:
        return jsonify({'success': False, 'message': result.get('error', 'Failed to complete project')}), 500
    
    return jsonify({
        'success': True,
        'message': 'Project completed successfully',
        'total_citations': result.get('total_citations', 0)
    })

@citations_api.route('/projects/<int:project_id>/export', methods=['GET'])
@token_required
def export_citations(current_user, project_id):
    """Export citations to a file."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Get query parameters
    format_type = request.args.get('format', 'csv')
    limit = request.args.get('limit')
    if limit:
        try:
            limit = int(limit)
        except ValueError:
            limit = None
    
    # Export citations
    success, message, file_path = ml_service.export_citations(project_id, format_type, limit)
    
    if not success or not file_path:
        return jsonify({'success': False, 'message': message}), 500
    
    # Return the file
    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path),
        mimetype='text/csv' if format_type == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@citations_api.route('/projects/<int:project_id>/stats', methods=['GET'])
@token_required
def get_project_stats(current_user, project_id):
    """Get project statistics."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Get citation counts
    total_citations = Citation.query.filter_by(project_id=project_id).count()
    labeled_citations = Citation.query.filter_by(project_id=project_id).filter(Citation.is_relevant.isnot(None)).count()
    
    # Get training iterations
    iterations = TrainingIteration.query.filter_by(project_id=project_id).order_by(TrainingIteration.iteration_number).all()
    
    # Format iterations
    iteration_data = []
    for iteration in iterations:
        # Get selections for this iteration
        relevant_count = TrainingSelection.query.filter_by(iteration_id=iteration.id, is_relevant=True).count()
        irrelevant_count = TrainingSelection.query.filter_by(iteration_id=iteration.id, is_relevant=False).count()
        
        iteration_data.append({
            'iteration_number': iteration.iteration_number,
            'relevant_count': relevant_count,
            'irrelevant_count': irrelevant_count,
            'created_at': iteration.created_at.isoformat() if iteration.created_at else None
        })
    
    return jsonify({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'status': project.status,
            'current_iteration': project.current_iteration or 0,
            'created_at': project.created_at.isoformat() if project.created_at else None,
            'updated_at': project.updated_at.isoformat() if project.updated_at else None
        },
        'citation_stats': {
            'total': total_citations,
            'labeled': labeled_citations,
            'unlabeled': total_citations - labeled_citations
        },
        'iterations': iteration_data
    })

@citations_api.route('/projects/<int:project_id>/next-batch', methods=['GET'])
@token_required
def get_next_citations_batch(current_user, project_id):
    """
    Get the next batch of citations for user review.
    This returns citations for the top (highest probability) and bottom (lowest probability)
    to make it easier for the user to select relevant and irrelevant examples.
    """
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Get the 15 highest scored citations
    top_citations = ml_service.get_sorted_citations(project_id, 'desc', 15)
    
    # Get the 15 lowest scored citations
    bottom_citations = ml_service.get_sorted_citations(project_id, 'asc', 15)
    
    return jsonify({
        'success': True,
        'top_citations': top_citations,
        'bottom_citations': bottom_citations,
        'current_iteration': project.current_iteration or 0
    })

@citations_api.route('/projects/<int:project_id>/citations/<int:citation_id>/toggle-relevance', methods=['POST'])
@token_required
def toggle_citation_relevance(current_user, project_id, citation_id):
    """Toggle the relevance of a citation (for manual labeling)."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Get the citation
    citation = Citation.query.filter_by(id=citation_id, project_id=project_id).first()
    
    if not citation:
        return jsonify({'success': False, 'message': 'Citation not found'}), 404
    
    # Toggle relevance
    data = request.json
    is_relevant = data.get('is_relevant')
    
    if is_relevant is not None:
        citation.is_relevant = bool(is_relevant)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'citation_id': citation.id,
        'is_relevant': citation.is_relevant
    })

@citations_api.route('/projects/<int:project_id>/citation-count', methods=['GET'])
@token_required
def get_citation_count(current_user, project_id):
    """Get the total number of citations for a project."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Count citations
    total_count = Citation.query.filter_by(project_id=project_id).count()
    
    return jsonify({
        'success': True,
        'total_count': total_count
    })

@citations_api.route('/projects/<int:project_id>/download-options', methods=['GET'])
@token_required
def get_download_options(current_user, project_id):
    """Get download options for a project."""
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    
    if not project:
        return jsonify({'success': False, 'message': 'Project not found or access denied'}), 404
    
    # Count citations
    total_count = Citation.query.filter_by(project_id=project_id).count()
    
    # Generate download options
    options = [
        {'value': 'all', 'label': f'All citations ({total_count})'},
        {'value': '100', 'label': 'Top 100 citations'},
        {'value': '200', 'label': 'Top 200 citations'},
        {'value': '500', 'label': 'Top 500 citations'}
    ]
    
    # Add custom options for larger datasets
    if total_count > 500:
        options.append({'value': '1000', 'label': 'Top 1000 citations'})
    
    if total_count > 1000:
        options.append({'value': '2000', 'label': 'Top 2000 citations'})
    
    return jsonify({
        'success': True,
        'options': options,
        'formats': [
            {'value': 'csv', 'label': 'CSV'},
            {'value': 'excel', 'label': 'Excel'}
        ]
    })
