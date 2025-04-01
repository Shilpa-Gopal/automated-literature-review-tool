import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
from collections import Counter
import spacy
import re
from typing import List, Dict, Tuple

class KeywordExtractor:
    """
    Extract keywords from a collection of citations using TF-IDF and other NLP techniques.
    """
    
    def __init__(self, max_keywords: int = 30):
        self.max_keywords = max_keywords
        try:
            # Load a spaCy model for additional NLP processing
            self.nlp = spacy.load("en_core_web_sm")
        except:
            # If model not available, download it
            import subprocess
            subprocess.call(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text for better keyword extraction."""
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces between words
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_keywords_from_citations(self, citations: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """
        Extract potential include and exclude keywords from a dataframe of citations.
        
        Args:
            citations: DataFrame with 'title' and 'abstract' columns
            
        Returns:
            Tuple of (include_keywords, exclude_keywords)
        """
        # Combine title and abstract for processing
        combined_text = citations.apply(
            lambda x: f"{str(x.get('title', '') or '')} {str(x.get('abstract', '') or '')}", 
            axis=1
        )
        
        # Preprocess text
        combined_text = combined_text.apply(self.preprocess_text)
        
        # Extract keywords using various methods
        tfidf_keywords = self._extract_tfidf_keywords(combined_text)
        ngram_keywords = self._extract_ngram_keywords(combined_text)
        entity_keywords = self._extract_entity_keywords(combined_text)
        
        # Combine all keywords
        all_keywords = list(set(tfidf_keywords + ngram_keywords + entity_keywords))
        
        # For demo purposes, we'll split keywords into include/exclude based on frequency
        # In a real-world scenario, this would use more sophisticated classification
        keyword_frequencies = Counter()
        for text in combined_text:
            for keyword in all_keywords:
                if keyword.lower() in text.lower():
                    keyword_frequencies[keyword] += 1
        
        sorted_keywords = sorted(keyword_frequencies.items(), key=lambda x: x[1], reverse=True)
        
        # Get top keywords
        top_keywords = [k for k, _ in sorted_keywords[:min(len(sorted_keywords), self.max_keywords)]]
        
        # For demonstration, we'll split into include/exclude based on some heuristics
        # In a real system, you'd want to use domain knowledge or ML to determine this split
        include_keywords = []
        exclude_keywords = []
        
        common_exclude_patterns = [
            'mice', 'mouse', 'rat', 'animal', 'in vitro', 'cell', 'review', 
            'meta analysis', 'meta-analysis', 'case report'
        ]
        
        for keyword in top_keywords:
            # Check if keyword matches common exclusion patterns
            if any(pattern in keyword.lower() for pattern in common_exclude_patterns):
                exclude_keywords.append(keyword)
            else:
                include_keywords.append(keyword)
        
        return include_keywords, exclude_keywords
    
    def _extract_tfidf_keywords(self, texts: pd.Series) -> List[str]:
        """Extract keywords using TF-IDF."""
        # Create a TF-IDF vectorizer
        tfidf = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)  # Include both unigrams and bigrams
        )
        
        # Fit and transform the text data
        tfidf_matrix = tfidf.fit_transform(texts)
        
        # Get feature names (words)
        feature_names = tfidf.get_feature_names_out()
        
        # Get average TF-IDF score for each word across all documents
        avg_tfidf_scores = tfidf_matrix.mean(axis=0).tolist()[0]
        
        # Pair feature names with their scores
        keyword_scores = list(zip(feature_names, avg_tfidf_scores))
        
        # Sort by score and get top keywords
        sorted_keywords = sorted(keyword_scores, key=lambda x: x[1], reverse=True)
        top_keywords = [keyword for keyword, _ in sorted_keywords[:50]]
        
        return top_keywords
    
    def _extract_ngram_keywords(self, texts: pd.Series) -> List[str]:
        """Extract important n-grams using frequency."""
        # Join all texts
        all_text = " ".join(texts.tolist())
        
        # Process with spaCy
        doc = self.nlp(all_text)
        
        # Extract noun phrases
        noun_phrases = []
        for chunk in doc.noun_chunks:
            if 2 <= len(chunk.text.split()) <= 3:  # Get 2-3 word phrases
                cleaned_chunk = self.preprocess_text(chunk.text)
                if len(cleaned_chunk.split()) >= 2:  # Ensure still multiword after cleaning
                    noun_phrases.append(cleaned_chunk)
        
        # Count frequencies
        phrase_counter = Counter(noun_phrases)
        
        # Get top phrases
        top_phrases = [phrase for phrase, _ in phrase_counter.most_common(30)]
        
        return top_phrases
    
    def _extract_entity_keywords(self, texts: pd.Series) -> List[str]:
        """Extract named entities from texts."""
        # Join a sample of texts (for efficiency)
        sample_size = min(50, len(texts))
        sample_texts = texts.sample(sample_size) if len(texts) > sample_size else texts
        
        all_text = " ".join(sample_texts.tolist())
        
        # Process with spaCy
        doc = self.nlp(all_text)
        
        # Extract entities of relevant types
        entities = []
        relevant_types = {'DISEASE', 'CHEMICAL', 'ORG', 'GPE', 'PRODUCT'}
        
        for ent in doc.ents:
            if ent.label_ in relevant_types:
                entities.append(ent.text.lower())
        
        # Count frequencies
        entity_counter = Counter(entities)
        
        # Get top entities
        top_entities = [entity for entity, _ in entity_counter.most_common(20)]
        
        return top_entities

    def suggest_keywords_for_biomedical_research(self) -> Tuple[List[str], List[str]]:
        """
        Suggest common keywords for biomedical research when citation data is insufficient.
        
        Returns:
            Tuple of (include_keywords, exclude_keywords)
        """
        include_keywords = [
            'clinical trial', 'randomized controlled trial', 'cohort study',
            'case control study', 'observational study', 'prospective study',
            'retrospective study', 'double blind', 'placebo controlled',
            'crossover design', 'follow up', 'survival analysis',
            'hazard ratio', 'odds ratio', 'risk ratio', 'confidence interval',
            'statistical significance', 'p value', 'efficacy', 'effectiveness',
            'biomarker', 'genetic marker', 'mutation', 'polymorphism',
            'cancer', 'tumor', 'neoplasm', 'carcinoma', 'treatment outcome',
            'disease progression', 'mortality', 'morbidity', 'recurrence',
            'metastasis', 'lymph node', 'human subjects', 'patients'
        ]
        
        exclude_keywords = [
            'in vitro', 'cell line', 'cell culture', 'mouse model', 'mice',
            'rat', 'animal model', 'animal study', 'case report',
            'meta analysis', 'systematic review', 'literature review',
            'editorial', 'letter', 'comment', 'guideline', 'protocol',
            'questionnaire', 'survey', 'interview', 'focus group',
            'computational model', 'simulation', 'algorithm',
            'theoretical model', 'mathematical model'
        ]
        
        return include_keywords, exclude_keywords