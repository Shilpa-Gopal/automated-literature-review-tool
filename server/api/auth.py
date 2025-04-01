from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt
)
import bcrypt
from datetime import datetime, timezone
from ..models.user import User
from ..models import db
from server.utils.validators import validate_email, validate_password


auth_api = Blueprint('auth_api', __name__)

@auth_api.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    # Get request data
    data = request.json
    
    # Validate required fields
    required_fields = ['email', 'password', 'firstName', 'lastName']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    # Extract and validate data
    email = data['email'].lower().strip()
    password = data['password']
    first_name = data['firstName'].strip()
    last_name = data['lastName'].strip()
    institution = data.get('institution', '').strip()
    
    # Validate email format
    if not validate_email(email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    # Validate password strength
    if not validate_password(password):
        return jsonify({
            'success': False, 
            'message': 'Password must be at least 6 characters long'
        }), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Email already registered'}), 409
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create new user
    new_user = User(
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
        institution=institution
    )
    
    try:
        # Add user to database
        db.session.add(new_user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=new_user.id)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'firstName': new_user.first_name,
                'lastName': new_user.last_name,
                'institution': new_user.institution
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'}), 500

@auth_api.route('/login', methods=['POST'])
def login():
    """Authenticate a user and issue JWT token."""
    # Get request data
    data = request.json
    
    # Validate required fields
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'success': False, 'message': 'Email and password required'}), 400
    
    # Extract data
    email = data['email'].lower().strip()
    password = data['password']
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    # Check if user exists and password is correct
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'access_token': access_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'institution': user.institution
        }
    })

@auth_api.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get the current user's profile."""
    # Get current user ID from JWT
    current_user_id = get_jwt_identity()
    
    # Find user
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'institution': user.institution,
            'createdAt': user.created_at.isoformat() if user.created_at else None
        }
    })

@auth_api.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update the current user's profile."""
    # Get current user ID from JWT
    current_user_id = get_jwt_identity()
    
    # Find user
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Get request data
    data = request.json
    
    # Update fields if provided
    if 'firstName' in data and data['firstName']:
        user.first_name = data['firstName'].strip()
    
    if 'lastName' in data and data['lastName']:
        user.last_name = data['lastName'].strip()
    
    if 'institution' in data:
        user.institution = data['institution'].strip()
    
    # Update password if provided
    if 'password' in data and data['password']:
        # Validate password strength
        if not validate_password(data['password']):
            return jsonify({
                'success': False, 
                'message': 'Password must be at least 6 characters long'
            }), 400
        
        # Hash password
        user.password_hash = bcrypt.hashpw(
            data['password'].encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    try:
        # Save changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'institution': user.institution
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Update failed: {str(e)}'}), 500

# Utility function for token verification in other blueprints
def token_required(f):
    """Decorator for endpoints that require authentication."""
    @jwt_required()
    def decorated(*args, **kwargs):
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return f(current_user, *args, **kwargs)
    
    # Preserve the original function name
    decorated.__name__ = f.__name__
    return decorated