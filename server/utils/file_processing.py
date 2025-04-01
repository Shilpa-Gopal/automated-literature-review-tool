import pandas as pd
import os
import logging
from typing import Dict, List, Tuple, Optional, Any
from werkzeug.utils import secure_filename

# Set up logger
logger = logging.getLogger(__name__)

def allowed_file(filename: str) -> bool:
    """
    Check if a file has an allowed extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        Whether the file is allowed
    """
    ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_citation_file(file_path: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Validate that a file is a valid citation dataset.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (is_valid, error_message, dataframe)
    """
    try:
        # Check file extension
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            return False, "Unsupported file format. Please upload a CSV or Excel file.", None
        
        # Check if the dataframe is empty
        if df.empty:
            return False, "The uploaded file is empty.", None
        
        # Standardize column names (lowercase)
        df.columns = [col.lower() for col in df.columns]
        
        # Check for required columns (title and abstract)
        title_col = None
        abstract_col = None
        
        for col in df.columns:
            if 'title' in col.lower():
                title_col = col
            elif 'abstract' in col.lower():
                abstract_col = col
        
        if not title_col:
            return False, "The dataset must contain a 'title' column.", None
        
        if not abstract_col:
            return False, "The dataset must contain an 'abstract' column.", None
        
        # Standardize column names
        column_mapping = {title_col: 'title', abstract_col: 'abstract'}
        df = df.rename(columns=column_mapping)
        
        # Check for empty values in required columns
        if df['title'].isnull().all():
            return False, "All title values are missing.", None
        
        if df['abstract'].isnull().all():
            return False, "All abstract values are missing.", None
        
        # Check if we have at least some non-empty rows
        valid_rows = (~df['title'].isnull()) | (~df['abstract'].isnull())
        if valid_rows.sum() < 5:
            return False, "Less than 5 valid citations found. Please check your data.", None
        
        # Success
        return True, "", df
        
    except Exception as e:
        logger.error(f"Error validating citation file: {str(e)}")
        return False, f"Error processing file: {str(e)}", None

def save_uploaded_file(file, upload_dir: str) -> Tuple[bool, str, Optional[str]]:
    """
    Save an uploaded file to disk.
    
    Args:
        file: Uploaded file object
        upload_dir: Directory to save the file in
        
    Returns:
        Tuple of (success, message, file_path)
    """
    try:
        # Check if file exists
        if not file:
            return False, "No file provided", None
        
        # Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Secure the filename
        filename = secure_filename(file.filename)
        if not filename:
            return False, "Invalid filename", None
        
        # Check file extension
        if not allowed_file(filename):
            return False, "File type not allowed. Please upload CSV or Excel files.", None
        
        # Save the file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return True, "File saved successfully", file_path
        
    except Exception as e:
        logger.error(f"Error saving uploaded file: {str(e)}")
        return False, f"Error saving file: {str(e)}", None

def convert_to_csv(df: pd.DataFrame, output_path: str) -> Tuple[bool, str]:
    """
    Convert a DataFrame to CSV and save it.
    
    Args:
        df: DataFrame to convert
        output_path: Path to save the CSV file
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        return True, "CSV file created successfully"
        
    except Exception as e:
        logger.error(f"Error converting to CSV: {str(e)}")
        return False, f"Error creating CSV file: {str(e)}"

def convert_to_excel(df: pd.DataFrame, output_path: str) -> Tuple[bool, str]:
    """
    Convert a DataFrame to Excel and save it.
    
    Args:
        df: DataFrame to convert
        output_path: Path to save the Excel file
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        
        return True, "Excel file created successfully"
        
    except Exception as e:
        logger.error(f"Error converting to Excel: {str(e)}")
        return False, f"Error creating Excel file: {str(e)}"

def get_file_info(file_path: str) -> Dict:
    """
    Get information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {'success': False, 'message': 'File not found'}
        
        # Get file stats
        stats = os.stat(file_path)
        
        # Get file extension
        _, ext = os.path.splitext(file_path)
        
        # Get file type and row count
        if ext.lower() == '.csv':
            df = pd.read_csv(file_path)
            file_type = 'CSV'
        elif ext.lower() in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
            file_type = 'Excel'
        else:
            return {'success': False, 'message': 'Unsupported file type'}
        
        # Get column info
        columns = list(df.columns)
        
        return {
            'success': True,
            'filename': os.path.basename(file_path),
            'file_type': file_type,
            'size_bytes': stats.st_size,
            'size_kb': round(stats.st_size / 1024, 2),
            'created': stats.st_ctime,
            'modified': stats.st_mtime,
            'row_count': len(df),
            'column_count': len(columns),
            'columns': columns
        }
        
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return {'success': False, 'message': f"Error getting file info: {str(e)}"}