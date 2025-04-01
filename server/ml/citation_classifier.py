import pandas as pd
import numpy as np
from xgboost import XGBClassifier, DMatrix, train, Booster
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, accuracy_score, precision_recall_curve
from sklearn.cluster import KMeans
from scipy import sparse
import pickle
import os
import logging
from typing import Dict, Tuple, List, Optional, Any, Union

class CitationClassifier:
    """
    A classifier for determining citation relevance in systematic literature reviews.
    
    This classifier implements an iterative active learning approach where:
    1. Keywords are used for initial scoring (before any labeled data exists)
    2. Initial samples are selected for user labeling
    3. Model is trained based on user feedback
    4. Predictions are made on remaining citations
    5. Next batch of uncertain citations is selected for labeling
    6. Process repeats until user is satisfied
    
    No labeled dataset is required initially. The system learns from user interactions.
    """
    
    def __init__(self, include_keywords: List[str] = None, exclude_keywords: List[str] = None, 
                 max_features: int = 30, random_state: int = 42):
        """
        Initialize the citation classifier.
        
        Args:
            include_keywords: List of keywords that indicate relevance
            exclude_keywords: List of keywords that indicate irrelevance
            max_features: Maximum number of features to use in TF-IDF vectorizer
            random_state: Random seed for reproducibility
        """
        self.max_features = max_features
        self.random_state = random_state
        self.samples_per_class = 5  # Initial samples per class (5 relevant, 5 irrelevant)
        self.booster = None  # XGBoost model (initialized after first training)
        
        # Store keywords
        self.keywords = {
            'include_keywords': include_keywords or [],
            'exclude_keywords': exclude_keywords or []
        }
        
        # Initialize vectorizer with keywords (if provided)
        if include_keywords or exclude_keywords:
            vocabulary = (include_keywords or []) + (exclude_keywords or [])
            self.vectorizer = TfidfVectorizer(
                vocabulary=vocabulary,
                ngram_range=(1, 2),
                stop_words='english'
            )
        else:
            # No keywords provided, use a standard vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=max_features,
                ngram_range=(1, 2),
                stop_words='english'
            )
        
        # XGBoost parameters
        self.model_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'learning_rate': 0.1,
            'max_depth': 6,
            'min_child_weight': 1,
            'gamma': 0,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': random_state
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
    
    def prepare_features(self, data: pd.DataFrame, is_training: bool = False) -> sparse.csr_matrix:
        """
        Extract features from citation data.
        
        Args:
            data: DataFrame containing 'title' and 'abstract' columns
            is_training: Whether this is for training (fit_transform) or prediction (transform)
            
        Returns:
            Sparse matrix of features
        """
        # Check required columns and fallback to empty strings if missing
        data = data.copy()
        if 'title' not in data.columns:
            data['title'] = ''
        if 'abstract' not in data.columns:
            data['abstract'] = ''
        
        # Combine title and abstract for text features
        # Handle NaN values and convert to string
        combined_text = data.apply(
            lambda x: f"{str(x['title'] or '')} {str(x['abstract'] or '')}",
            axis=1
        )
        
        # Extract keyword features
        if is_training:
            keyword_features = self.vectorizer.fit_transform(combined_text)
        else:
            try:
                keyword_features = self.vectorizer.transform(combined_text)
            except Exception as e:
                # If vocabulary hasn't been fitted yet
                self.logger.warning(f"Vectorizer not fitted, fitting now: {str(e)}")
                keyword_features = self.vectorizer.fit_transform(combined_text)
        
        # Add additional features
        # Abstract word count
        data['abstract_word_count'] = data['abstract'].apply(
            lambda x: len(str(x).split()) if pd.notna(x) else 0
        )
        
        # Title word count
        data['title_word_count'] = data['title'].apply(
            lambda x: len(str(x).split()) if pd.notna(x) else 0
        )
        
        # Add more features if available in the data
        feature_columns = ['abstract_word_count', 'title_word_count']
        
        # If year is available, use it as a feature
        if 'year' in data.columns:
            # Replace missing years with median
            if data['year'].isna().any():
                median_year = data['year'].median()
                data['year'] = data['year'].fillna(median_year)
            feature_columns.append('year')
        
        additional_features = data[feature_columns].values
        
        # Combine all features
        return sparse.hstack([keyword_features, sparse.csr_matrix(additional_features)])
    
    def run_initial_keyword_scoring(self, citations: pd.DataFrame) -> pd.DataFrame:
        """
        Score citations based on keyword presence when no model exists yet.
        This provides an initial ranking before any user labeling.
        
        Args:
            citations: DataFrame of citations with 'title' and 'abstract' columns
            
        Returns:
            DataFrame with added 'initial_score' column, sorted by score
        """
        scored_citations = citations.copy()
        
        # Initialize score (neutral starting point)
        scored_citations['initial_score'] = 0.5
        
        # Define weight for title and abstract matches
        title_weight = 0.05   # Higher weight for title matches
        abstract_weight = 0.02  # Lower weight for abstract matches
        
        # Count keywords in title and abstract
        for keyword in self.keywords['include_keywords']:
            keyword_lower = keyword.lower()
            
            # Title matches (higher weight)
            scored_citations['initial_score'] += scored_citations['title'].apply(
                lambda x: title_weight if pd.notna(x) and keyword_lower in str(x).lower() else 0
            )
            
            # Abstract matches (lower weight)
            scored_citations['initial_score'] += scored_citations['abstract'].apply(
                lambda x: abstract_weight if pd.notna(x) and keyword_lower in str(x).lower() else 0
            )
        
        # Subtract score for exclude keywords
        for keyword in self.keywords['exclude_keywords']:
            keyword_lower = keyword.lower()
            
            # Title matches (higher weight)
            scored_citations['initial_score'] -= scored_citations['title'].apply(
                lambda x: title_weight if pd.notna(x) and keyword_lower in str(x).lower() else 0
            )
            
            # Abstract matches (lower weight)
            scored_citations['initial_score'] -= scored_citations['abstract'].apply(
                lambda x: abstract_weight if pd.notna(x) and keyword_lower in str(x).lower() else 0
            )
        
        # Clip scores to [0, 1] range
        scored_citations['initial_score'] = scored_citations['initial_score'].clip(0, 1)
        
        # If we have relevance_score column, use initial_score to populate it
        if 'relevance_score' in scored_citations.columns:
            scored_citations['relevance_score'] = scored_citations['initial_score']
        
        # Sort by score
        return scored_citations.sort_values(by='initial_score', ascending=False)
    
    def select_initial_citations(self, citations: pd.DataFrame, sample_method: str = 'keyword_based') -> pd.DataFrame:
        """
        Select initial citations for user labeling when no labeled data exists.
        
        Args:
            citations: DataFrame of citations
            sample_method: Method for initial selection ('random', 'diverse', 'keyword_based')
            
        Returns:
            DataFrame with selected citations
        """
        # If we have keywords, run initial scoring
        if self.keywords['include_keywords'] or self.keywords['exclude_keywords']:
            scored_citations = self.run_initial_keyword_scoring(citations)
        else:
            scored_citations = citations.copy()
            # Assign neutral score if no keywords available
            scored_citations['initial_score'] = 0.5
        
        if sample_method == 'random':
            # Simple random sampling
            return citations.sample(min(30, len(citations)), random_state=self.random_state)
        
        elif sample_method == 'diverse':
            # Use clustering to select diverse samples
            X = self.prepare_features(citations)
            
            # Determine number of clusters based on data size
            n_clusters = min(30, len(citations))
            
            # Apply K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=self.random_state).fit(X)
            
            # Add cluster labels to citations
            citations_with_clusters = citations.copy()
            citations_with_clusters['cluster'] = kmeans.labels_
            
            # Select one sample from each cluster
            samples = citations_with_clusters.groupby('cluster').apply(
                lambda x: x.sample(1, random_state=self.random_state)
            ).reset_index(drop=True)
            
            return samples
        
        elif sample_method == 'keyword_based':
            # Select samples based on keyword score distribution
            # For best results, we want a mix of high, medium, and low scoring citations
            
            # Sort by keyword score
            sorted_df = scored_citations.sort_values(by='initial_score', ascending=False)
            
            # Get counts
            n_high = 10   # Top 10 highest scores
            n_low = 10    # Bottom 10 lowest scores
            n_mid = 10    # 10 from middle scores
            
            # Select high scoring samples (likely relevant)
            high_scoring = sorted_df.head(n_high)
            
            # Select low scoring samples (likely irrelevant)
            low_scoring = sorted_df.tail(n_low)
            
            # Select medium scoring samples (uncertain)
            if len(sorted_df) > n_high + n_low:
                mid_idx = len(sorted_df) // 2
                mid_start = max(0, mid_idx - n_mid // 2)
                mid_end = min(len(sorted_df), mid_idx + n_mid // 2)
                mid_scoring = sorted_df.iloc[mid_start:mid_end]
            else:
                # Not enough data for mid section
                mid_scoring = pd.DataFrame(columns=sorted_df.columns)
            
            # Combine all selections
            combined = pd.concat([high_scoring, mid_scoring, low_scoring])
            
            # Remove duplicates (in case of overlap)
            combined = combined.drop_duplicates(subset=['id'] if 'id' in combined.columns else None)
            
            return combined
        
        else:
            self.logger.warning(f"Unknown sampling method '{sample_method}', using random sampling.")
            return citations.sample(min(30, len(citations)), random_state=self.random_state)
    
    def train_initial_model(self, labeled_data: pd.DataFrame) -> Dict:
        """
        Train the initial model with the first batch of labeled data.
        
        Args:
            labeled_data: DataFrame with 'title', 'abstract', and 'is_relevant' columns
            
        Returns:
            Dictionary with training metrics and indices
        """
        # Verify we have sufficient labeled data
        if len(labeled_data) < 10:
            raise ValueError("Insufficient training data. Need at least 10 labeled citations.")
        
        # Make sure we have both relevant and irrelevant examples
        relevance_counts = labeled_data['is_relevant'].value_counts()
        if len(relevance_counts) < 2 or relevance_counts.min() < 5:
            raise ValueError("Need at least 5 examples of each class (relevant and irrelevant).")
        
        # Split data into training and test sets (use only labeled data)
        labeled_data = labeled_data.dropna(subset=['is_relevant']).copy()
        
        # Select samples for training (at least 5 from each class)
        relevant = labeled_data[labeled_data['is_relevant'] == True].head(self.samples_per_class)
        irrelevant = labeled_data[labeled_data['is_relevant'] == False].head(self.samples_per_class)
        
        # Combine training data
        train_data = pd.concat([relevant, irrelevant])
        
        # Use remaining labeled data for evaluation
        test_data = labeled_data[~labeled_data.index.isin(train_data.index)]
        
        # If test set is empty, use training data for evaluation (not ideal but necessary for very small datasets)
        if len(test_data) == 0:
            self.logger.warning("No separate test data available. Using training data for evaluation.")
            test_data = train_data.copy()
        
        # Extract features
        X_train = self.prepare_features(train_data, is_training=True)
        y_train = train_data['is_relevant'].astype(int).values
        
        X_test = self.prepare_features(test_data)
        y_test = test_data['is_relevant'].astype(int).values
        
        # Train XGBoost model
        dtrain = DMatrix(X_train, label=y_train)
        dtest = DMatrix(X_test, label=y_test)
        
        # Adjust positive class weight based on class distribution
        pos_count = np.sum(y_train == 1)
        neg_count = np.sum(y_train == 0)
        
        if pos_count > 0 and neg_count > 0:
            self.model_params['scale_pos_weight'] = neg_count / pos_count
        
        # Set evaluation metrics
        evals = [(dtrain, 'train'), (dtest, 'eval')]
        
        # Train the model
        self.booster = train(
            self.model_params,
            dtrain,
            num_boost_round=100,
            early_stopping_rounds=10,
            evals=evals,
            verbose_eval=False
        )
        
        # Get predictions on test set
        y_test_probs = self.booster.predict(dtest)
        
        # Store indices of training samples
        train_indices = train_data.index.tolist()
        
        # Return training results
        return {
            'training_samples': len(train_data),
            'train_indices': train_indices
        }
    
    def update_model(self, labeled_data: pd.DataFrame, previously_used_indices: List) -> Dict:
        """
        Update the model with new labeled samples.
        
        Args:
            labeled_data: DataFrame with 'title', 'abstract', and 'is_relevant' columns
            previously_used_indices: Indices of samples already used for training
            
        Returns:
            Dictionary with training indices
        """
        if self.booster is None:
            raise ValueError("Model has not been initialized. Call train_initial_model first.")
        
        # Update the labeled dataset
        labeled_data = labeled_data.dropna(subset=['is_relevant']).copy()
        
        # Combine all training data (previous + new)
        train_data = labeled_data.loc[previously_used_indices + 
                                     [idx for idx in labeled_data.index if idx not in previously_used_indices 
                                      and pd.notna(labeled_data.loc[idx, 'is_relevant'])]]
        
        # Rest of the data for testing
        test_data = labeled_data[~labeled_data.index.isin(train_data.index)]
        
        # If test set is empty, use a subset of training data
        if len(test_data) == 0:
            self.logger.warning("No separate test data available. Using subset of training data for evaluation.")
            # Use 20% of training data for testing
            train_indices = train_data.index.tolist()
            test_indices = train_indices[:max(1, len(train_indices) // 5)]
            test_data = train_data.loc[test_indices]
        
        # Extract features
        X_train = self.prepare_features(train_data, is_training=True)
        y_train = train_data['is_relevant'].astype(int).values
        
        X_test = self.prepare_features(test_data)
        y_test = test_data['is_relevant'].astype(int).values
        
        # Train updated XGBoost model
        dtrain = DMatrix(X_train, label=y_train)
        dtest = DMatrix(X_test, label=y_test)
        
        # Adjust positive class weight
        pos_count = np.sum(y_train == 1)
        neg_count = np.sum(y_train == 0)
        
        if pos_count > 0 and neg_count > 0:
            self.model_params['scale_pos_weight'] = neg_count / pos_count
        
        # Set evaluation metrics
        evals = [(dtrain, 'train'), (dtest, 'eval')]
        
        # Train the model
        self.booster = train(
            self.model_params,
            dtrain,
            num_boost_round=100,
            early_stopping_rounds=10,
            evals=evals,
            verbose_eval=False
        )
        
        # Store indices of all training samples
        train_indices = train_data.index.tolist()
        
        # Return training results
        return {
            'training_samples': len(train_data),
            'train_indices': train_indices
        }
    
    def predict_relevance(self, citations: pd.DataFrame) -> pd.DataFrame:
        """
        Predict relevance scores for citations.
        
        Args:
            citations: DataFrame with 'title' and 'abstract' columns
            
        Returns:
            DataFrame with added 'relevance_score' column (sorted by score)
        """
        # If model doesn't exist yet, use keyword scoring
        if self.booster is None:
            self.logger.warning("No trained model available. Using keyword-based scoring.")
            return self.run_initial_keyword_scoring(citations)
        
        # Create a copy to avoid modifying the original
        result = citations.copy()
        
        # Extract features
        X = self.prepare_features(result)
        dmatrix = DMatrix(X)
        
        # Make predictions
        result['relevance_score'] = self.booster.predict(dmatrix)
        
        # Sort by relevance score in descending order (highest first)
        result = result.sort_values(by='relevance_score', ascending=False)
        
        return result
    
    def _select_samples_for_labeling(self, remaining_data: pd.DataFrame, method: str = 'uncertainty') -> pd.DataFrame:
        """
        Select the next batch of samples for user labeling.
        
        Args:
            remaining_data: DataFrame with 'predicted_prob' or 'relevance_score' column
            method: Selection strategy ('uncertainty', 'entropy', or 'diversity')
            
        Returns:
            DataFrame with selected samples
        """
        remaining_data = remaining_data.copy()
        
        # Make sure we have a score column
        score_col = 'predicted_prob' if 'predicted_prob' in remaining_data.columns else 'relevance_score'
        
        if score_col not in remaining_data.columns:
            raise ValueError(f"Missing score column '{score_col}' in data")
        
        # Rename to predicted_prob for consistency
        if score_col != 'predicted_prob':
            remaining_data['predicted_prob'] = remaining_data[score_col]
        
        if method == 'uncertainty':
            # Sort by uncertainty (closest to 0.5)
            remaining_data['uncertainty'] = np.abs(remaining_data['predicted_prob'] - 0.5)
            sorted_data = remaining_data.sort_values(by='uncertainty', ascending=True)
            return sorted_data.head(self.samples_per_class * 2)
            
        elif method == 'entropy':
            # Calculate entropy (highest entropy at p=0.5)
            remaining_data['entropy'] = - (
                remaining_data['predicted_prob'] * np.log2(remaining_data['predicted_prob'] + 1e-8) +
                (1 - remaining_data['predicted_prob']) * np.log2(1 - remaining_data['predicted_prob'] + 1e-8)
            )
            sorted_data = remaining_data.sort_values(by='entropy', ascending=False)
            return sorted_data.head(self.samples_per_class * 2)
            
        elif method == 'diversity':
            # Use K-means clustering to select diverse uncertain samples
            # First filter to get samples with moderate uncertainty
            uncertain_samples = remaining_data[
                (remaining_data['predicted_prob'] >= 0.3) & 
                (remaining_data['predicted_prob'] <= 0.7)
            ]
            
            if len(uncertain_samples) < self.samples_per_class:
                # Not enough uncertain samples, use uncertainty method
                self.logger.warning("Not enough uncertain samples for diversity sampling. Using uncertainty method.")
                return self._select_samples_for_labeling(remaining_data, method='uncertainty')
            
            # Extract features
            X_uncertain = self.prepare_features(uncertain_samples)
            
            # Apply K-means clustering
            n_clusters = min(self.samples_per_class * 2, len(uncertain_samples))
            kmeans = KMeans(n_clusters=n_clusters, random_state=self.random_state).fit(X_uncertain)
            
            # Add cluster labels
            uncertain_samples['cluster'] = kmeans.labels_
            
            # Select one sample from each cluster
            selected_samples = uncertain_samples.groupby('cluster').apply(
                lambda x: x.sample(1, random_state=self.random_state)
            ).reset_index(drop=True)
            
            return selected_samples
        
        else:
            self.logger.warning(f"Unknown sampling method '{method}', using uncertainty sampling.")
            return self._select_samples_for_labeling(remaining_data, method='uncertainty')

    def save_model(self, filepath: str) -> None:
        """Save the model to a file."""
        if self.booster is None:
            raise ValueError("No model to save")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save XGBoost model
        self.booster.save_model(filepath)
        
        # Save vectorizer and other parameters
        params = {
            'keywords': self.keywords,
            'max_features': self.max_features,
            'random_state': self.random_state,
            'model_params': self.model_params
        }
        
        with open(f"{filepath}_params.pkl", 'wb') as f:
            pickle.dump(params, f)
        
        # Save vectorizer separately (it can be large)
        with open(f"{filepath}_vectorizer.pkl", 'wb') as f:
            pickle.dump(self.vectorizer, f)
    
    def load_model(self, filepath: str) -> None:
        """Load a model from file."""
        # Load XGBoost model
        self.booster = Booster()
        self.booster.load_model(filepath)
        
        # Load parameters
        with open(f"{filepath}_params.pkl", 'rb') as f:
            params = pickle.load(f)
        
        self.keywords = params['keywords']
        self.max_features = params['max_features']
        self.random_state = params['random_state']
        self.model_params = params['model_params']
        
        # Load vectorizer
        with open(f"{filepath}_vectorizer.pkl", 'rb') as f:
            self.vectorizer = pickle.load(f)
    
    def get_feature_importance(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Get the most important features for classification.
        
        Args:
            top_n: Number of top features to return
            
        Returns:
            List of (feature_name, importance_score) tuples
        """
        if self.booster is None:
            raise ValueError("No trained model available")
        
        # Get feature names from vectorizer
        feature_names = self.vectorizer.get_feature_names_out().tolist()
        
        # Add additional feature names
        feature_names.extend(['abstract_word_count', 'title_word_count'])
        
        # Get feature importance scores
        importance_scores = self.booster.get_score(importance_type='gain')
        
        # Convert feature indices to names
        feature_importance = []
        for feature_idx, score in importance_scores.items():
            # Feature indices in XGBoost are f0, f1, f2, etc.
            idx = int(feature_idx.replace('f', ''))
            if idx < len(feature_names):
                feature_importance.append((feature_names[idx], score))
        
        # Sort by importance (highest first)
        sorted_importance = sorted(feature_importance, key=lambda x: x[1], reverse=True)
        
        # Return top N features
        return sorted_importance[:top_n]
    
    def get_model_summary(self) -> Dict:
        """
        Get a summary of the current model state.
        
        Returns:
            Dictionary with model information
        """
        if self.booster is None:
            return {
                'status': 'Not trained',
                'keywords': self.keywords
            }
        
        # Get feature importance
        try:
            top_features = self.get_feature_importance(10)
        except:
            top_features = []
        
        # Model parameters
        model_params = self.model_params.copy()
        
        return {
            'status': 'Trained',
            'keywords': self.keywords,
            'top_features': top_features,
            'model_params': model_params
        }
    
    def stratified_sample_for_review(self, citations: pd.DataFrame, n_samples: int = 30) -> pd.DataFrame:
        """
        Select a stratified sample of citations for user review.
        This is useful for evaluating the model's performance.
        
        Args:
            citations: DataFrame with 'relevance_score' column
            n_samples: Number of samples to select
            
        Returns:
            DataFrame with selected citations
        """
        if 'relevance_score' not in citations.columns:
            # If no relevance scores available, predict them
            scored_citations = self.predict_relevance(citations)
        else:
            scored_citations = citations.copy()
        
        # Create score bins
        scored_citations['score_bin'] = pd.cut(
            scored_citations['relevance_score'], 
            bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
            labels=['very_low', 'low', 'medium', 'high', 'very_high']
        )
        
        # Determine number of samples per bin
        samples_per_bin = max(1, n_samples // 5)
        
        # Select samples from each bin
        selected_samples = []
        for bin_label in ['very_low', 'low', 'medium', 'high', 'very_high']:
            bin_samples = scored_citations[scored_citations['score_bin'] == bin_label]
            
            if len(bin_samples) > 0:
                # Select samples (or all if fewer than requested)
                n_select = min(samples_per_bin, len(bin_samples))
                selected = bin_samples.sample(n_select, random_state=self.random_state)
                selected_samples.append(selected)
        
        # Combine all selected samples
        if selected_samples:
            combined = pd.concat(selected_samples)
            
            # Drop the temporary bin column
            combined = combined.drop(columns=['score_bin'])
            
            return combined
        else:
            # If no samples were selected (unlikely), return a random sample
            return scored_citations.sample(min(n_samples, len(scored_citations)), random_state=self.random_state)

    def get_top_and_bottom_citations(self, citations: pd.DataFrame, top_n: int = 15, bottom_n: int = 15) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get the top N and bottom N citations based on relevance score.
        
        Args:
            citations: DataFrame with citations
            top_n: Number of top (highest relevance) citations to return
            bottom_n: Number of bottom (lowest relevance) citations to return
            
        Returns:
            Tuple of (top_citations, bottom_citations) DataFrames
        """
        # Ensure we have relevance scores
        if 'relevance_score' not in citations.columns:
            # If no relevance scores available, predict them
            citations_with_scores = self.predict_relevance(citations)
        else:
            citations_with_scores = citations.copy()
        
        # Sort by relevance score
        sorted_citations = citations_with_scores.sort_values(by='relevance_score', ascending=False)
        
        # Get top and bottom citations
        top_citations = sorted_citations.head(top_n)
        bottom_citations = sorted_citations.tail(bottom_n)
        
        return top_citations, bottom_citations  