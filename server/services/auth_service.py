import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from ..models.user import User
from ..models.project import Project
from ..models.citation import Citation,TrainingSelection
from ..utils.validators import validate_email, validate_password

class AuthService:
    """Service for user authentication and account management."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def register_user(self, email: str, password: str, first_name: str, 
                     last_name: str, institution: str = None) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: User's password
            first_name: User's first name
            last_name: User's last name
            institution: User's institution (optional)
            
        Returns:
            Tuple of (success, message, user)
        """
        try:
            # Validate email
            if not validate_email(email):
                return False, "Invalid email format", None
            
            # Validate password
            if not validate_password(password):
                return False, "Password must be at least 6 characters", None
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email.lower()).first()
            if existing_user:
                return False, "Email already registered", None
            
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create new user
            user = User(
                email=email.lower(),
                password_hash=hashed_password,
                first_name=first_name,
                last_name=last_name,
                institution=institution
            )
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            return True, "User registered successfully", user
            
        except Exception as e:
            self.logger.error(f"Error registering user: {str(e)}")
            db.session.rollback()
            return False, f"Registration failed: {str(e)}", None
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate a user.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple of (success, message, user)
        """
        try:
            # Find user by email
            user = User.query.filter_by(email=email.lower()).first()
            
            # Check if user exists
            if not user:
                return False, "Invalid email or password", None
            
            # Check password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                return False, "Invalid email or password", None
            
            return True, "Authentication successful", user
            
        except Exception as e:
            self.logger.error(f"Error authenticating user: {str(e)}")
            return False, f"Authentication failed: {str(e)}", None
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change a user's password.
        
        Args:
            user_id: ID of the user
            current_password: Current password
            new_password: New password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Find user
            user = User.query.get(user_id)
            
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
                return False, "Current password is incorrect"
            
            # Validate new password
            if not validate_password(new_password):
                return False, "New password must be at least 6 characters"
            
            # Hash and save new password
            user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.session.commit()
            
            return True, "Password updated successfully"
            
        except Exception as e:
            self.logger.error(f"Error changing password: {str(e)}")
            db.session.rollback()
            return False, f"Password change failed: {str(e)}"
    
    def update_profile(self, user_id: int, first_name: str = None, 
                      last_name: str = None, institution: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Update a user's profile.
        
        Args:
            user_id: ID of the user
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            institution: User's institution (optional)
            
        Returns:
            Tuple of (success, message, updated_profile)
        """
        try:
            # Find user
            user = User.query.get(user_id)
            
            if not user:
                return False, "User not found", None
            
            # Update fields if provided
            if first_name is not None:
                user.first_name = first_name
            
            if last_name is not None:
                user.last_name = last_name
            
            if institution is not None:
                user.institution = institution
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Return updated profile
            profile = {
                'id': user.id,
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'institution': user.institution
            }
            
            return True, "Profile updated successfully", profile
            
        except Exception as e:
            self.logger.error(f"Error updating profile: {str(e)}")
            db.session.rollback()
            return False, f"Profile update failed: {str(e)}", None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User object or None
        """
        return User.query.get(user_id)