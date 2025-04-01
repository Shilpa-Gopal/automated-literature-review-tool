import pandas as pd
import logging
import os
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

from ..models.user import User
from ..models.project import Project
from ..models.citation import Citation,TrainingSelection
from ..ml.citation_classifier import CitationClassifier

class CitationService:
    """Service for managing citations and citation-related operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def import_citations_from_file(self, project_id: int, file_path: str) -> Tuple[bool, str, int]:
        """
        Import citations from a file into a project.
        
        Args:
            project_id: ID of the project
            file_path: Path to the citation file (CSV or Excel)
            
        Returns:
            Tuple of (success, message, citation_count)
        """
        try:
            # Check file type and read
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                return False, "Unsupported file format. Please upload a CSV or Excel file.", 0
            
            # Check if dataframe is empty
            if df.empty:
                return False, "The uploaded file is empty.", 0
            
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
                return False, "The dataset must contain a 'title' column.", 0
            
            if not abstract_col:
                return False, "The dataset must contain an 'abstract' column.", 0
            
            # Standardize column names
            column_mapping = {title_col: 'title', abstract_col: 'abstract'}
            df = df.rename(columns=column_mapping)
            
            # Get the project
            project = Project.query.get(project_id)
            if not project:
                return False, f"Project with ID {project_id} not found.", 0
            
            # Process each row
            citation_count = 0
            for _, row in df.iterrows():
                # Ensure title and abstract are not NaN
                title = row['title'] if pd.notna(row['title']) else ""
                abstract = row['abstract'] if pd.notna(row['abstract']) else ""
                
                # Get optional fields
                authors = row.get('authors', "") if pd.notna(row.get('authors', "")) else ""
                year = int(row['year']) if 'year' in row and pd.notna(row['year']) else None
                journal = row.get('journal', "") if pd.notna(row.get('journal', "")) else ""
                
                # Create JSON of all original data
                raw_data = {}
                for col in df.columns:
                    if pd.notna(row[col]):
                        raw_data[col] = row[col]
                
                # Create citation
                citation = Citation(
                    project_id=project_id,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    year=year,
                    journal=journal,
                    raw_data=raw_data,
                    relevance_score=0.5  # Neutral initial score
                )
                
                db.session.add(citation)
                citation_count += 1
            
            # Update project status if needed
            if project.status == 'created' or not project.status:
                project.status = 'imported'
            
            # Save changes
            db.session.commit()
            
            return True, f"Successfully imported {citation_count} citations.", citation_count
            
        except Exception as e:
            self.logger.error(f"Error importing citations: {str(e)}")
            db.session.rollback()
            return False, f"Error importing citations: {str(e)}", 0
    
    def get_citations(self, project_id: int, sort_by: str = 'relevance', 
                     sort_order: str = 'desc', limit: Optional[int] = None) -> List[Dict]:
        """
        Get citations for a project with sorting options.
        
        Args:
            project_id: ID of the project
            sort_by: Field to sort by (relevance, title, year)
            sort_order: Sort order (asc or desc)
            limit: Optional limit on number of citations
            
        Returns:
            List of citation dictionaries
        """
        try:
            # Determine sort field and order
            if sort_by == 'relevance':
                sort_field = Citation.relevance_score
            elif sort_by == 'title':
                sort_field = Citation.title
            elif sort_by == 'year':
                sort_field = Citation.year
            else:
                sort_field = Citation.relevance_score
            
            # Determine sort order
            if sort_order == 'asc':
                order_clause = sort_field.asc()
            else:
                order_clause = sort_field.desc()
            
            # Query citations
            query = Citation.query.filter_by(project_id=project_id).order_by(order_clause)
            
            # Apply limit if provided
            if limit:
                query = query.limit(limit)
            
            citations = query.all()
            
            # Format as dictionaries
            citation_list = []
            for citation in citations:
                citation_dict = {
                    'id': citation.id,
                    'title': citation.title,
                    'abstract': citation.abstract,
                    'authors': citation.authors,
                    'year': citation.year,
                    'journal': citation.journal,
                    'relevance_score': citation.relevance_score,
                    'is_relevant': citation.is_relevant
                }
                citation_list.append(citation_dict)
            
            return citation_list
            
        except Exception as e:
            self.logger.error(f"Error getting citations: {str(e)}")
            return []
    
    def get_citation_by_id(self, citation_id: int) -> Optional[Dict]:
        """
        Get a citation by ID.
        
        Args:
            citation_id: ID of the citation
            
        Returns:
            Citation dictionary or None
        """
        try:
            citation = Citation.query.get(citation_id)
            
            if not citation:
                return None
            
            return {
                'id': citation.id,
                'project_id': citation.project_id,
                'title': citation.title,
                'abstract': citation.abstract,
                'authors': citation.authors,
                'year': citation.year,
                'journal': citation.journal,
                'relevance_score': citation.relevance_score,
                'is_relevant': citation.is_relevant,
                'raw_data': citation.raw_data
            }
            
        except Exception as e:
            self.logger.error(f"Error getting citation: {str(e)}")
            return None
    
    def update_citation_relevance(self, citation_id: int, is_relevant: bool) -> Tuple[bool, str]:
        """
        Update the relevance of a citation (for manual labeling).
        
        Args:
            citation_id: ID of the citation
            is_relevant: Whether the citation is relevant
            
        Returns:
            Tuple of (success, message)
        """
        try:
            citation = Citation.query.get(citation_id)
            
            if not citation:
                return False, "Citation not found"
            
            citation.is_relevant = is_relevant
            db.session.commit()
            
            return True, "Citation relevance updated successfully"
            
        except Exception as e:
            self.logger.error(f"Error updating citation relevance: {str(e)}")
            db.session.rollback()
            return False, f"Error updating citation relevance: {str(e)}"
    
    def get_citations_for_review(self, project_id: int, batch_size: int = 10) -> Dict:
        """
        Get citations for review, both high and low scoring ones.
        
        Args:
            project_id: ID of the project
            batch_size: Number of citations to get from each end
            
        Returns:
            Dict with top and bottom citations
        """
        try:
            # Get top (highest relevance) citations
            top_citations = Citation.query.filter_by(project_id=project_id) \
                .filter(Citation.is_relevant.is_(None)) \
                .order_by(Citation.relevance_score.desc()) \
                .limit(batch_size).all()
            
            # Get bottom (lowest relevance) citations
            bottom_citations = Citation.query.filter_by(project_id=project_id) \
                .filter(Citation.is_relevant.is_(None)) \
                .order_by(Citation.relevance_score.asc()) \
                .limit(batch_size).all()
            
            # Format as dictionaries
            top_list = []
            for citation in top_citations:
                top_list.append({
                    'id': citation.id,
                    'title': citation.title,
                    'abstract': citation.abstract,
                    'authors': citation.authors,
                    'year': citation.year,
                    'journal': citation.journal,
                    'relevance_score': citation.relevance_score
                })
            
            bottom_list = []
            for citation in bottom_citations:
                bottom_list.append({
                    'id': citation.id,
                    'title': citation.title,
                    'abstract': citation.abstract,
                    'authors': citation.authors,
                    'year': citation.year,
                    'journal': citation.journal,
                    'relevance_score': citation.relevance_score
                })
            
            return {
                'top_citations': top_list,
                'bottom_citations': bottom_list
            }
            
        except Exception as e:
            self.logger.error(f"Error getting citations for review: {str(e)}")
            return {'top_citations': [], 'bottom_citations': []}
    
    def record_training_selections(self, project_id: int, iteration: int, 
                                 relevant_ids: List[int], irrelevant_ids: List[int]) -> Tuple[bool, str]:
        """
        Record user selections for a training iteration.
        
        Args:
            project_id: ID of the project
            iteration: Training iteration number
            relevant_ids: IDs of citations marked as relevant
            irrelevant_ids: IDs of citations marked as irrelevant
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if project exists
            project = Project.query.get(project_id)
            if not project:
                return False, "Project not found"
            
            # Create training iteration record
            training_iteration = TrainingIteration(
                project_id=project_id,
                iteration_number=iteration
            )
            
            db.session.add(training_iteration)
            db.session.flush()  # Get ID without committing
            
            # Record selections
            for citation_id in relevant_ids:
                # Update citation relevance
                citation = Citation.query.get(citation_id)
                if citation:
                    citation.is_relevant = True
                    
                    # Record selection
                    selection = TrainingSelection(
                        iteration_id=training_iteration.id,
                        citation_id=citation_id,
                        is_relevant=True
                    )
                    db.session.add(selection)
            
            for citation_id in irrelevant_ids:
                # Update citation relevance
                citation = Citation.query.get(citation_id)
                if citation:
                    citation.is_relevant = False
                    
                    # Record selection
                    selection = TrainingSelection(
                        iteration_id=training_iteration.id,
                        citation_id=citation_id,
                        is_relevant=False
                    )
                    db.session.add(selection)
            
            # Update project
            project.current_iteration = iteration
            db.session.commit()
            
            return True, "Training selections recorded successfully"
            
        except Exception as e:
            self.logger.error(f"Error recording training selections: {str(e)}")
            db.session.rollback()
            return False, f"Error recording training selections: {str(e)}"
    
    def export_citations(self, project_id: int, format_type: str = 'csv', 
                        limit: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Export citations to a file.
        
        Args:
            project_id: ID of the project
            format_type: Export format ('csv' or 'excel')
            limit: Optional limit on number of citations to export
            
        Returns:
            Tuple of (success, message, file_path)
        """
        try:
            # Get project
            project = Project.query.get(project_id)
            if not project:
                return False, "Project not found", None
            
            # Get sorted citations
            query = Citation.query.filter_by(project_id=project_id).order_by(Citation.relevance_score.desc())
            
            # Apply limit if specified
            if limit:
                try:
                    limit = int(limit)
                    query = query.limit(limit)
                except ValueError:
                    # If limit is not a valid integer, ignore it
                    pass
            
            citations = query.all()
            
            if not citations:
                return False, "No citations to export", None
            
            # Create DataFrame
            data = []
            for citation in citations:
                # Start with basic fields
                citation_dict = {
                    'id': citation.id,
                    'title': citation.title,
                    'abstract': citation.abstract,
                    'authors': citation.authors,
                    'year': citation.year,
                    'journal': citation.journal,
                    'relevance_score': citation.relevance_score,
                    'is_relevant': 'Yes' if citation.is_relevant == True else 
                                ('No' if citation.is_relevant == False else 'Unknown')
                }
                
                # Add raw data fields if available (but don't duplicate)
                if citation.raw_data:
                    for key, value in citation.raw_data.items():
                        if key not in citation_dict and key not in ['title', 'abstract', 'authors', 'year', 'journal']:
                            citation_dict[key] = value
                
                data.append(citation_dict)
            
            df = pd.DataFrame(data)
            
            # Create export directory if it doesn't exist
            export_dir = os.path.join('exports', str(project_id))
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            project_name = project.name.replace(' ', '_')
            filename = f"{project_name}_citations_{timestamp}"
            
            # Export to file
            if format_type.lower() == 'csv':
                file_path = os.path.join(export_dir, f"{filename}.csv")
                df.to_csv(file_path, index=False)
            elif format_type.lower() == 'excel':
                file_path = os.path.join(export_dir, f"{filename}.xlsx")
                df.to_excel(file_path, index=False)
            else:
                return False, f"Unsupported export format: {format_type}", None
            
            return True, f"Successfully exported {len(citations)} citations", file_path
            
        except Exception as e:
            self.logger.error(f"Error exporting citations: {str(e)}")
            return False, f"Error exporting citations: {str(e)}", None
    
    def get_citation_stats(self, project_id: int) -> Dict:
        """
        Get statistics about citations in a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with citation statistics
        """
        try:
            # Get total count
            total_count = Citation.query.filter_by(project_id=project_id).count()
            
            # Get labeled count
            labeled_count = Citation.query.filter_by(project_id=project_id).filter(
                Citation.is_relevant.isnot(None)
            ).count()
            
            # Get relevant count
            relevant_count = Citation.query.filter_by(project_id=project_id, is_relevant=True).count()
            
            # Get irrelevant count
            irrelevant_count = Citation.query.filter_by(project_id=project_id, is_relevant=False).count()
            
            # Calculate average relevance score
            avg_score_query = db.session.query(db.func.avg(Citation.relevance_score)) \
                .filter(Citation.project_id == project_id)
            avg_score = avg_score_query.scalar() or 0
            
            return {
                'total_count': total_count,
                'labeled_count': labeled_count,
                'unlabeled_count': total_count - labeled_count,
                'relevant_count': relevant_count,
                'irrelevant_count': irrelevant_count,
                'average_relevance_score': float(avg_score)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting citation stats: {str(e)}")
            return {
                'total_count': 0,
                'labeled_count': 0,
                'unlabeled_count': 0,
                'relevant_count': 0,
                'irrelevant_count': 0,
                'average_relevance_score': 0
            }
