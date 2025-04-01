import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd

from ..models.user import User
from ..models.project import Project
from ..models.citation import Citation,TrainingSelection
from ..ml.keyword_extractor import KeywordExtractor

class KeywordService:
    """Service for keyword extraction and management."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.keyword_extractor = KeywordExtractor(max_keywords=30)
    
    def extract_keywords_from_project(self, project_id: int) -> Tuple[List[str], List[str]]:
        """
        Extract potential keywords from a project's citations.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Tuple of (include_keywords, exclude_keywords)
        """
        try:
            # Get citations
            citations = Citation.query.filter_by(project_id=project_id).all()
            
            if not citations or len(citations) < 3:
                # Not enough citations for meaningful extraction, use defaults
                self.logger.warning(f"Not enough citations in project {project_id} for keyword extraction")
                return self.keyword_extractor.suggest_keywords_for_biomedical_research()
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'title': citation.title,
                'abstract': citation.abstract
            } for citation in citations])
            
            # Extract keywords
            include_keywords, exclude_keywords = self.keyword_extractor.extract_keywords_from_citations(df)
            
            return include_keywords, exclude_keywords
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {str(e)}")
            # Fallback to default keywords
            return self.keyword_extractor.suggest_keywords_for_biomedical_research()
    
    def update_project_keywords(self, project_id: int, include_keywords: List[str], 
                              exclude_keywords: List[str]) -> bool:
        """
        Update a project's keywords.
        
        Args:
            project_id: ID of the project
            include_keywords: List of keywords to include
            exclude_keywords: List of keywords to exclude
            
        Returns:
            Success flag
        """
        try:
            # Get project
            project = Project.query.get(project_id)
            
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return False
            
            # Update keywords
            project.include_keywords = include_keywords
            project.exclude_keywords = exclude_keywords
            
            # Save changes
            db.session.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating project keywords: {str(e)}")
            db.session.rollback()
            return False
    
    def get_project_keywords(self, project_id: int) -> Tuple[Optional[List[str]], Optional[List[str]]]:
        """
        Get a project's keywords.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Tuple of (include_keywords, exclude_keywords)
        """
        try:
            # Get project
            project = Project.query.get(project_id)
            
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return None, None
            
            return project.include_keywords, project.exclude_keywords
            
        except Exception as e:
            self.logger.error(f"Error getting project keywords: {str(e)}")
            return None, None
    
    def analyze_keyword_effectiveness(self, project_id: int) -> Dict:
        """
        Analyze the effectiveness of keywords in identifying relevant citations.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with keyword effectiveness analysis
        """
        try:
            # Get project
            project = Project.query.get(project_id)
            
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return {'success': False, 'message': 'Project not found'}
            
            # Get include and exclude keywords
            include_keywords = project.include_keywords or []
            exclude_keywords = project.exclude_keywords or []
            
            if not include_keywords and not exclude_keywords:
                return {'success': False, 'message': 'No keywords defined for project'}
            
            # Get labeled citations
            relevant_citations = Citation.query.filter_by(project_id=project_id, is_relevant=True).all()
            irrelevant_citations = Citation.query.filter_by(project_id=project_id, is_relevant=False).all()
            
            if not relevant_citations or not irrelevant_citations:
                return {'success': False, 'message': 'Not enough labeled citations for analysis'}
            
            # Analyze include keywords
            include_keyword_stats = []
            for keyword in include_keywords:
                keyword_lower = keyword.lower()
                
                # Count occurrences in relevant citations
                relevant_count = sum(1 for citation in relevant_citations if 
                                   keyword_lower in (citation.title or '').lower() or 
                                   keyword_lower in (citation.abstract or '').lower())
                
                # Count occurrences in irrelevant citations
                irrelevant_count = sum(1 for citation in irrelevant_citations if 
                                     keyword_lower in (citation.title or '').lower() or 
                                     keyword_lower in (citation.abstract or '').lower())
                
                # Calculate precision (% of occurrences that are relevant)
                total_occurrences = relevant_count + irrelevant_count
                precision = relevant_count / total_occurrences if total_occurrences > 0 else 0
                
                # Calculate recall (% of relevant citations that contain the keyword)
                recall = relevant_count / len(relevant_citations) if relevant_citations else 0
                
                include_keyword_stats.append({
                    'keyword': keyword,
                    'relevant_count': relevant_count,
                    'irrelevant_count': irrelevant_count,
                    'precision': precision,
                    'recall': recall,
                    'effectiveness': precision * recall  # Combined measure
                })
            
            # Analyze exclude keywords
            exclude_keyword_stats = []
            for keyword in exclude_keywords:
                keyword_lower = keyword.lower()
                
                # Count occurrences in relevant citations
                relevant_count = sum(1 for citation in relevant_citations if 
                                   keyword_lower in (citation.title or '').lower() or 
                                   keyword_lower in (citation.abstract or '').lower())
                
                # Count occurrences in irrelevant citations
                irrelevant_count = sum(1 for citation in irrelevant_citations if 
                                     keyword_lower in (citation.title or '').lower() or 
                                     keyword_lower in (citation.abstract or '').lower())
                
                # Calculate precision (% of occurrences that are irrelevant)
                total_occurrences = relevant_count + irrelevant_count
                precision = irrelevant_count / total_occurrences if total_occurrences > 0 else 0
                
                # Calculate recall (% of irrelevant citations that contain the keyword)
                recall = irrelevant_count / len(irrelevant_citations) if irrelevant_citations else 0
                
                exclude_keyword_stats.append({
                    'keyword': keyword,
                    'relevant_count': relevant_count,
                    'irrelevant_count': irrelevant_count,
                    'precision': precision,
                    'recall': recall,
                    'effectiveness': precision * recall  # Combined measure
                })
            
            # Sort by effectiveness
            include_keyword_stats.sort(key=lambda x: x['effectiveness'], reverse=True)
            exclude_keyword_stats.sort(key=lambda x: x['effectiveness'], reverse=True)
            
            return {
                'success': True,
                'include_keywords': include_keyword_stats,
                'exclude_keywords': exclude_keyword_stats,
                'total_relevant': len(relevant_citations),
                'total_irrelevant': len(irrelevant_citations)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing keyword effectiveness: {str(e)}")
            return {'success': False, 'message': f"Error analyzing keyword effectiveness: {str(e)}"}
    
    def suggest_new_keywords(self, project_id: int) -> Dict:
        """
        Suggest new keywords based on current labeled citations.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with suggested keywords
        """
        try:
            # Get project
            project = Project.query.get(project_id)
            
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return {'success': False, 'message': 'Project not found'}
            
            # Get current keywords
            current_include = set(project.include_keywords or [])
            current_exclude = set(project.exclude_keywords or [])
            
            # Get labeled citations
            relevant_citations = Citation.query.filter_by(project_id=project_id, is_relevant=True).all()
            irrelevant_citations = Citation.query.filter_by(project_id=project_id, is_relevant=False).all()
            
            if not relevant_citations or not irrelevant_citations:
                return {'success': False, 'message': 'Not enough labeled citations for analysis'}
            
            # Extract keywords from relevant citations
            relevant_df = pd.DataFrame([{
                'title': citation.title,
                'abstract': citation.abstract
            } for citation in relevant_citations])
            
            # Extract keywords from irrelevant citations
            irrelevant_df = pd.DataFrame([{
                'title': citation.title,
                'abstract': citation.abstract
            } for citation in irrelevant_citations])
            
            # Extract keywords from each set
            relevant_keywords, _ = self.keyword_extractor.extract_keywords_from_citations(relevant_df)
            _, irrelevant_keywords = self.keyword_extractor.extract_keywords_from_citations(irrelevant_df)
            
            # Find new keywords (not in current sets)
            new_include_suggestions = [k for k in relevant_keywords if k.lower() not in 
                                     {x.lower() for x in current_include} and k.lower() not in 
                                     {x.lower() for x in current_exclude}]
            
            new_exclude_suggestions = [k for k in irrelevant_keywords if k.lower() not in 
                                     {x.lower() for x in current_include} and k.lower() not in 
                                     {x.lower() for x in current_exclude}]
            
            return {
                'success': True,
                'include_suggestions': new_include_suggestions[:10],  # Limit to top 10
                'exclude_suggestions': new_exclude_suggestions[:10]   # Limit to top 10
            }
            
        except Exception as e:
            self.logger.error(f"Error suggesting new keywords: {str(e)}")
            return {'success': False, 'message': f"Error suggesting new keywords: {str(e)}"}
    
    def search_citations_by_keyword(self, project_id: int, keyword: str) -> Dict:
        """
        Search for citations containing a specific keyword.
        
        Args:
            project_id: ID of the project
            keyword: Keyword to search for
            
        Returns:
            Dictionary with matching citations
        """
        try:
            # Get project
            project = Project.query.get(project_id)
            
            if not project:
                self.logger.error(f"Project {project_id} not found")
                return {'success': False, 'message': 'Project not found'}
            
            # Normalize keyword
            keyword_lower = keyword.lower()
            
            # Find citations containing the keyword
            matching_citations = []
            
            citations = Citation.query.filter_by(project_id=project_id).all()
            for citation in citations:
                if (keyword_lower in (citation.title or '').lower() or 
                    keyword_lower in (citation.abstract or '').lower()):
                    
                    matching_citations.append({
                        'id': citation.id,
                        'title': citation.title,
                        'abstract': citation.abstract,
                        'is_relevant': citation.is_relevant,
                        'relevance_score': citation.relevance_score
                    })
            
            return {
                'success': True,
                'keyword': keyword,
                'matching_citations': matching_citations,
                'total_matches': len(matching_citations)
            }
            
        except Exception as e:
            self.logger.error(f"Error searching citations by keyword: {str(e)}")
            return {'success': False, 'message': f"Error searching citations by keyword: {str(e)}"}