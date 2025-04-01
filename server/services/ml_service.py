import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Optional, Any
import logging
import json
from datetime import datetime

from ..ml.keyword_extractor import KeywordExtractor
from ..ml.citation_classifier import CitationClassifier
from ..models.user import User
from ..models.project import Project
from ..models.citation import Citation,TrainingSelection

class MLService:
    """Service for handling machine learning tasks in the literature review assistant."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Model cache to avoid reloading for the same project
        self.model_cache = {}
    
    def validate_citation_dataset(self, file_path: str) -> Tuple[bool, str, pd.DataFrame]:
        """
        Validate that the uploaded file is a valid citation dataset with required columns.
        
        Args:
            file_path: Path to the uploaded file
            
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
            
            # Check for required columns (title and abstract)
            # First, standardize column names (lowercase)
            df.columns = [col.lower() for col in df.columns]
            
            # Check if 'title' and 'abstract' columns exist (regardless of case)
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
            
            # Ensure all other columns are preserved
            return True, "", df
            
        except Exception as e:
            self.logger.error(f"Error validating citation dataset: {str(e)}")
            return False, f"Error processing file: {str(e)}", None
    
    def import_citations(self, project_id: int, df: pd.DataFrame) -> Tuple[bool, str, int]:
        """
        Import citations from a validated dataframe into the database.
        
        Args:
            project_id: The ID of the project
            df: DataFrame containing validated citation data
            
        Returns:
            Tuple of (success, message, citation_count)
        """
        try:
            project = Project.query.get(project_id)
            
            if not project:
                return False, f"Project with ID {project_id} not found.", 0
            
            # Process each row in the dataframe
            citation_count = 0
            for _, row in df.iterrows():
                # Create a new citation
                citation = Citation(
                    project_id=project_id,
                    title=row['title'] if pd.notna(row['title']) else "",
                    abstract=row['abstract'] if pd.notna(row['abstract']) else "",
                    # Optional fields - extract if available
                    authors=row.get('authors', "") if pd.notna(row.get('authors', "")) else "",
                    year=int(row['year']) if 'year' in row and pd.notna(row['year']) else None,
                    journal=row.get('journal', "") if pd.notna(row.get('journal', "")) else "",
                    # Store original row data as JSON
                    raw_data=row.to_dict(),
                    # Initialize relevance score to neutral
                    relevance_score=0.5
                )
                
                db.session.add(citation)
                citation_count += 1
            
            # Update project status
            project.status = 'created'
            db.session.commit()
            
            return True, f"Successfully imported {citation_count} citations.", citation_count
            
        except Exception as e:
            self.logger.error(f"Error importing citations: {str(e)}")
            db.session.rollback()
            return False, f"Error importing citations: {str(e)}", 0
    
    def extract_keywords_from_citations(self, project_id: int) -> Tuple[List[str], List[str]]:
        """
        Extract potential keywords from a project's citations.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Tuple of (include_keywords, exclude_keywords)
        """
        # Get the project's citations
        citations_data = Citation.query.filter_by(project_id=project_id).all()
        
        if len(citations_data) < 5:
            # Not enough citations for good keyword extraction
            self.logger.warning(f"Project {project_id} has too few citations for keyword extraction. Using default keywords.")
            
            # Initialize extractor with no citations
            extractor = KeywordExtractor(max_keywords=30)
            return extractor.suggest_keywords_for_biomedical_research()
        
        # Convert to DataFrame
        citations_df = pd.DataFrame([{
            'title': citation.title,
            'abstract': citation.abstract
        } for citation in citations_data])
        
        # Initialize keyword extractor
        extractor = KeywordExtractor(max_keywords=30)
        
        # Extract keywords
        include_keywords, exclude_keywords = extractor.extract_keywords_from_citations(citations_df)
        
        return include_keywords, exclude_keywords
    
    def update_project_keywords(self, project_id: int, include_keywords: List[str], exclude_keywords: List[str]) -> bool:
        """
        Update a project's keywords based on user selection.
        
        Args:
            project_id: The ID of the project
            include_keywords: The selected include keywords
            exclude_keywords: The selected exclude keywords
            
        Returns:
            Success flag
        """
        try:
            project = Project.query.get(project_id)
            
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False
            
            # Update project
            project.include_keywords = include_keywords
            project.exclude_keywords = exclude_keywords
            
            # Save to database
            db.session.commit()
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error updating project keywords: {str(e)}")
            db.session.rollback()
            return False
    
    def get_citations_for_initial_selection(self, project_id: int, count: int = 30) -> List[Dict]:
        """
        Get a batch of citations for initial user selection (5 relevant, 5 irrelevant).
        We'll try to get a diverse set to maximize the chance of finding both relevant and irrelevant examples.
        
        Args:
            project_id: The ID of the project
            count: Number of citations to return for selection
            
        Returns:
            List of citation dictionaries
        """
        project = Project.query.get(project_id)
        
        if not project:
            self.logger.error(f"Project {project_id} not found")
            return []
        
        # Get all citations for the project
        citations_data = Citation.query.filter_by(project_id=project_id).all()
        
        # Convert to DataFrame
        citations_df = pd.DataFrame([{
            'id': citation.id,
            'title': citation.title,
            'abstract': citation.abstract,
            'authors': citation.authors,
            'year': citation.year,
            'journal': citation.journal
        } for citation in citations_data])
        
        # If we have keywords, use them for initial scoring
        if project.include_keywords or project.exclude_keywords:
            # Initialize classifier with project keywords
            classifier = CitationClassifier(
                include_keywords=project.include_keywords or [],
                exclude_keywords=project.exclude_keywords or []
            )
            
            # Run initial keyword scoring
            scored_df = classifier.run_initial_keyword_scoring(citations_df)
            
            # Get diverse sample:
            # - 10 from highest scores (most likely relevant)
            # - 10 from lowest scores (most likely irrelevant)
            # - 10 from middle scores (uncertain)
            high_scoring = scored_df.head(10).to_dict('records')
            low_scoring = scored_df.tail(10).to_dict('records')
            
            # Get middle scoring
            middle_index = len(scored_df) // 2
            middle_range = 5  # Take 5 before and 5 after the middle
            middle_start = max(0, middle_index - middle_range)
            middle_end = min(len(scored_df), middle_index + middle_range)
            middle_scoring = scored_df.iloc[middle_start:middle_end].head(10).to_dict('records')
            
            # Combine and return
            return high_scoring + middle_scoring + low_scoring
        else:
            # No keywords available, just return a random sample
            return citations_df.sample(min(count, len(citations_df))).to_dict('records')
    
    def train_model_with_selected_citations(self, project_id: int, relevant_ids: List[int], 
                                           irrelevant_ids: List[int], iteration: int = 1) -> Dict:
        """
        Train or update the model with user-selected relevant and irrelevant citations.
        
        Args:
            project_id: The ID of the project
            relevant_ids: List of citation IDs marked as relevant
            irrelevant_ids: List of citation IDs marked as irrelevant
            iteration: Current training iteration
            
        Returns:
            Dictionary with training results
        """
        project = Project.query.get(project_id)
        
        if not project:
            self.logger.error(f"Project {project_id} not found")
            return {'success': False, 'error': 'Project not found'}
        
        # Ensure we have enough training data
        if len(relevant_ids) < 5 or len(irrelevant_ids) < 5:
            return {
                'success': False,
                'error': 'Insufficient training data. Please select at least 5 relevant and 5 irrelevant citations.'
            }
        
        # Get all citations for the project
        all_citations = Citation.query.filter_by(project_id=project_id).all()
        
        # Prepare data for training
        citations_df = pd.DataFrame([{
            'id': citation.id,
            'title': citation.title,
            'abstract': citation.abstract,
            'authors': citation.authors,
            'year': citation.year,
            'journal': citation.journal,
            'is_relevant': True if citation.id in relevant_ids else 
                         (False if citation.id in irrelevant_ids else None)
        } for citation in all_citations])
        
        # Filter to only include citations with known relevance
        labeled_df = citations_df.dropna(subset=['is_relevant'])
        
        # Initialize classifier
        classifier = CitationClassifier(
            include_keywords=project.include_keywords or [],
            exclude_keywords=project.exclude_keywords or []
        )
        
        try:
            # Check if this is the first iteration
            if iteration == 1:
                self.logger.info(f"Training initial model for project {project_id}")
                training_result = classifier.train_initial_model(labeled_df)
            else:
                # Get previous training iterations
                previous_iterations = TrainingIteration.query.filter_by(project_id=project_id).all()
                
                # Get all previously used citation IDs
                previously_used_ids = []
                for prev_iter in previous_iterations:
                    selections = TrainingSelection.query.filter_by(iteration_id=prev_iter.id).all()
                    previously_used_ids.extend([s.citation_id for s in selections])
                
                self.logger.info(f"Updating model for project {project_id}, iteration {iteration}")
                training_result = classifier.update_model(labeled_df, previously_used_ids)
            
            # Create training iteration record
            iteration_record = TrainingIteration(
                project_id=project_id,
                iteration_number=iteration
            )
            
            db.session.add(iteration_record)
            db.session.flush()  # Get ID without committing
            
            # Create training selection records
            for citation_id in relevant_ids:
                selection = TrainingSelection(
                    iteration_id=iteration_record.id,
                    citation_id=citation_id,
                    is_relevant=True
                )
                db.session.add(selection)
            
            for citation_id in irrelevant_ids:
                selection = TrainingSelection(
                    iteration_id=iteration_record.id,
                    citation_id=citation_id,
                    is_relevant=False
                )
                db.session.add(selection)
            
            # Update project
            project.status = 'in_progress'
            project.current_iteration = iteration
            
            # Run predictions on all citations
            predicted_df = classifier.predict_relevance(citations_df)
            
            # Update citation relevance scores in database
            for _, row in predicted_df.iterrows():
                citation = Citation.query.get(row['id'])
                if citation:
                    citation.relevance_score = float(row['relevance_score'])
                    # Update is_relevant for citations selected in this iteration
                    if citation.id in relevant_ids:
                        citation.is_relevant = True
                    elif citation.id in irrelevant_ids:
                        citation.is_relevant = False
            
            # Save model
            os.makedirs(f"models/{project_id}", exist_ok=True)
            classifier.save_model(f"models/{project_id}/model_iteration_{iteration}")
            
            # Store model in cache
            self.model_cache[project_id] = classifier
            
            # Commit changes
            db.session.commit()
            
            # Return sorted citations (top and bottom) for the next selection
            top_citations = predicted_df.sort_values(by='relevance_score', ascending=False).head(15).to_dict('records')
            bottom_citations = predicted_df.sort_values(by='relevance_score', ascending=True).head(15).to_dict('records')
            
            return {
                'success': True,
                'iteration': iteration,
                'top_citations': top_citations,
                'bottom_citations': bottom_citations
            }
            
        except Exception as e:
            self.logger.error(f"Error training model: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_sorted_citations(self, project_id: int, sort_order: str = 'desc', limit: Optional[int] = None) -> List[Dict]:
        """
        Get sorted citations based on relevance score.
        
        Args:
            project_id: The ID of the project
            sort_order: Sort order ('desc' for most relevant first, 'asc' for least relevant first)
            limit: Optional limit on number of citations to return
            
        Returns:
            List of sorted citation dictionaries
        """
        project = Project.query.get(project_id)
        
        if not project:
            self.logger.error(f"Project {project_id} not found")
            return []
        
        # Determine sort order
        order_clause = Citation.relevance_score.desc() if sort_order == 'desc' else Citation.relevance_score.asc()
        
        # Query citations with ordering
        query = Citation.query.filter_by(project_id=project_id).order_by(order_clause)
        
        # Apply limit if specified
        if limit:
            query = query.limit(limit)
        
        citations = query.all()
        
        # Convert to list of dictionaries
        citation_list = [{
            'id': citation.id,
            'title': citation.title,
            'abstract': citation.abstract,
            'authors': citation.authors,
            'year': citation.year,
            'journal': citation.journal,
            'relevance_score': citation.relevance_score,
            'is_relevant': citation.is_relevant
        } for citation in citations]
        
        return citation_list
    
    def complete_project(self, project_id: int) -> Dict:
        """
        Mark a project as completed and finalize rankings.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Dictionary with completion results
        """
        project = Project.query.get(project_id)
        
        if not project:
            self.logger.error(f"Project {project_id} not found")
            return {'success': False, 'error': 'Project not found'}
        
        try:
            # Update project status
            project.status = 'completed'
            project.updated_at = datetime.utcnow()
            
            # Commit changes
            db.session.commit()
            
            # Return rankings
            rankings = self.get_sorted_citations(project_id)
            
            return {
                'success': True,
                'total_citations': len(rankings)
            }
            
        except Exception as e:
            self.logger.error(f"Error completing project: {str(e)}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def export_citations(self, project_id: int, format_type: str = 'csv', 
                        limit: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Export citations to a file.
        
        Args:
            project_id: The ID of the project
            format_type: Export format ('csv' or 'excel')
            limit: Optional limit on number of citations to export
            
        Returns:
            Tuple of (success, message, file_path)
        """
        project = Project.query.get(project_id)
        
        if not project:
            self.logger.error(f"Project {project_id} not found")
            return False, "Project not found", None
        
        try:
            # Get sorted citations
            citations = self.get_sorted_citations(project_id, limit=limit)
            
            if not citations:
                return False, "No citations to export", None
            
            # Create DataFrame
            df = pd.DataFrame(citations)
            
            # Create export directory if it doesn't exist
            export_dir = os.path.join('exports', str(project_id))
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"citations_export_{timestamp}"
            
            if format_type == 'csv':
                file_path = os.path.join(export_dir, f"{filename}.csv")
                df.to_csv(file_path, index=False)
            elif format_type == 'excel':
                file_path = os.path.join(export_dir, f"{filename}.xlsx")
                df.to_excel(file_path, index=False)
            else:
                return False, "Unsupported export format", None
            
            return True, f"Successfully exported {len(citations)} citations", file_path
            
        except Exception as e:
            self.logger.error(f"Error exporting citations: {str(e)}")
            return False, f"Error exporting citations: {str(e)}", None