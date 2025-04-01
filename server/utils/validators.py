import re
from typing import Dict, List, Any, Optional

def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Whether the email is valid
    """
    if not email:
        return False
    
    # Simple regex for email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> bool:
    """
    Validate a password.
    
    Args:
        password: Password to validate
        
    Returns:
        Whether the password is valid
    """
    # Check length
    if not password or len(password) < 6:
        return False
    
    return True

def validate_project_name(name: str) -> bool:
    """
    Validate a project name.
    
    Args:
        name: Project name to validate
        
    Returns:
        Whether the name is valid
    """
    if not name or not name.strip():
        return False
    
    # Check length
    if len(name.strip()) < 3:
        return False
    
    return True

def validate_required_fields(data: Dict, required_fields: List[str]) -> Dict[str, str]:
    """
    Validate that required fields are present and not empty.
    
    Args:
        data: Dictionary of data to validate
        required_fields: List of required field names
        
    Returns:
        Dictionary of error messages for missing fields
    """
    errors = {}
    
    for field in required_fields:
        if field not in data:
            errors[field] = f"Field '{field}' is required"
        elif not data[field] and not isinstance(data[field], (int, float, bool)):
            errors[field] = f"Field '{field}' cannot be empty"
    
    return errors

def validate_integer(value: Any, min_value: Optional[int] = None, 
                   max_value: Optional[int] = None) -> bool:
    """
    Validate that a value is an integer within an optional range.
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        Whether the value is valid
    """
    try:
        # Convert to integer
        int_value = int(value)
        
        # Check range if specified
        if min_value is not None and int_value < min_value:
            return False
        
        if max_value is not None and int_value > max_value:
            return False
        
        return True
        
    except (ValueError, TypeError):
        return False

def validate_float(value: Any, min_value: Optional[float] = None, 
                 max_value: Optional[float] = None) -> bool:
    """
    Validate that a value is a float within an optional range.
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        Whether the value is valid
    """
    try:
        # Convert to float
        float_value = float(value)
        
        # Check range if specified
        if min_value is not None and float_value < min_value:
            return False
        
        if max_value is not None and float_value > max_value:
            return False
        
        return True
        
    except (ValueError, TypeError):
        return False

def validate_string_length(value: str, min_length: Optional[int] = None, 
                         max_length: Optional[int] = None) -> bool:
    """
    Validate that a string is within a length range.
    
    Args:
        value: String to validate
        min_length: Minimum allowed length (optional)
        max_length: Maximum allowed length (optional)
        
    Returns:
        Whether the string is valid
    """
    if not isinstance(value, str):
        return False
    
    # Check length range
    if min_length is not None and len(value) < min_length:
        return False
    
    if max_length is not None and len(value) > max_length:
        return False
    
    return True

def validate_list_length(value: List, min_length: Optional[int] = None, 
                       max_length: Optional[int] = None) -> bool:
    """
    Validate that a list is within a length range.
    
    Args:
        value: List to validate
        min_length: Minimum allowed length (optional)
        max_length: Maximum allowed length (optional)
        
    Returns:
        Whether the list is valid
    """
    if not isinstance(value, list):
        return False
    
    # Check length range
    if min_length is not None and len(value) < min_length:
        return False
    
    if max_length is not None and len(value) > max_length:
        return False
    
    return True

def validate_in_options(value: Any, options: List[Any]) -> bool:
    """
    Validate that a value is one of the allowed options.
    
    Args:
        value: Value to validate
        options: List of allowed options
        
    Returns:
        Whether the value is valid
    """
    return value in options

def validate_citation_format(citation: Dict) -> Dict[str, str]:
    """
    Validate the format of a citation.
    
    Args:
        citation: Citation dictionary to validate
        
    Returns:
        Dictionary of validation errors
    """
    errors = {}
    
    # Check required fields
    if 'title' not in citation or not citation['title']:
        errors['title'] = "Title is required"
    
    if 'abstract' not in citation:
        errors['abstract'] = "Abstract is required"
    
    # Check types
    if 'year' in citation and citation['year']:
        try:
            year = int(citation['year'])
            current_year = 2025  # Use a future year to allow newer publications
            if year < 1900 or year > current_year:
                errors['year'] = f"Year must be between 1900 and {current_year}"
        except (ValueError, TypeError):
            errors['year'] = "Year must be a valid number"
    
    return errors
