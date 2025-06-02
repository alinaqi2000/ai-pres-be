from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from sqlalchemy.orm import Session
from database.models import SearchHistory
from database.models.user_model import User

class PropertyRecommendationSystem:
    """
    AI-based recommendation system that matches new properties/units
    with user search history to generate relevant notifications.
    """
    
    def __init__(self, model_path="recommendation_models"):
        """Initialize the recommendation system."""
        self.model_path = model_path
        self.tfidf_vectorizer = None
        self.search_history_df = None
        self.users_df = None
        
        # Create model directory if it doesn't exist
        if not os.path.exists(model_path):
            os.makedirs(model_path)
    
    def preprocess_search_history(self, db: Session) -> pd.DataFrame:
        """Extract and preprocess user search history data."""
        # Get all search history from the last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        search_history = db.query(SearchHistory).filter(
            SearchHistory.created_at >= thirty_days_ago
        ).all()
        
        # Convert to DataFrame
        search_data = []
        for sh in search_history:
            search_data.append({
                'id': sh.id,
                'user_id': sh.user_id,
                'query_name': sh.query_name or '',
                'query_city': sh.query_city or '',
                'monthly_rent_gt': sh.monthly_rent_gt or 0,
                'monthly_rent_lt': sh.monthly_rent_lt or float('inf'),
                'created_at': sh.created_at
            })
        
        search_df = pd.DataFrame(search_data)
        return search_df
    
    def preprocess_users(self, db: Session) -> pd.DataFrame:
        """Extract user data."""
        users = db.query(User).all()
        
        user_data = []
        for user in users:
            user_data.append({
                'id': user.id,
                'email': user.email if hasattr(user, 'email') else '',
                'notification_preference': user.notification_preference if hasattr(user, 'notification_preference') else True
            })
        
        user_df = pd.DataFrame(user_data)
        return user_df
    
    def create_text_features(self, search_df: pd.DataFrame) -> pd.DataFrame:
        """Create text features from search history for content-based filtering."""
        # Create a combined text feature for TF-IDF
        search_df['text_features'] = search_df.apply(
            lambda row: f"{row['query_name']} {row['query_city']}", axis=1
        )
        
        return search_df
    
    def train_model(self, db: Session) -> None:
        """Train the recommendation model using search history data."""
        print("Starting model training...")
        
        # Get and preprocess data
        self.search_history_df = self.preprocess_search_history(db)
        self.users_df = self.preprocess_users(db)
        
        if len(self.search_history_df) == 0:
            print("No search history data available for training.")
            return
        
        # Create text features
        self.search_history_df = self.create_text_features(self.search_history_df)
        
        # Add a default token to prevent empty vocabulary
        # Ensure text features are not empty
        self.search_history_df['text_features'] = self.search_history_df['text_features'].apply(
            lambda x: x if x.strip() else 'default_token'
        )
        
        # Create and fit TF-IDF vectorizer on search text
        self.tfidf_vectorizer = TfidfVectorizer(
            min_df=1, 
            stop_words='english',
            lowercase=True,
            analyzer='word',
            token_pattern=r'(?u)\b\w+\b'  # Less strict token pattern to include more words
        )
        
        try:
            # Fit the vectorizer
            self.tfidf_vectorizer.fit(self.search_history_df['text_features'].values)
        except ValueError as e:
            print(f"Error fitting vectorizer: {e}")
            # Create a simple vectorizer with no filtering as fallback
            self.tfidf_vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words=None,
                token_pattern=r'(?u)\b\w\w*\b',  # Match any word with at least one character
                min_df=0
            )
            # Add a dummy document if we have no valid text
            texts = list(self.search_history_df['text_features'].values)
            if not texts or all(not text.strip() for text in texts):
                texts.append("default_token")
            self.tfidf_vectorizer.fit(texts)
        
        # Save the model
        joblib.dump(self.tfidf_vectorizer, os.path.join(self.model_path, 'tfidf_vectorizer.pkl'))
        self.search_history_df.to_pickle(os.path.join(self.model_path, 'search_history.pkl'))
        self.users_df.to_pickle(os.path.join(self.model_path, 'users.pkl'))
        
        print("Model training completed and saved.")
    
    def load_model(self) -> bool:
        """Load the trained recommendation model."""
        try:
            self.tfidf_vectorizer = joblib.load(os.path.join(self.model_path, 'tfidf_vectorizer.pkl'))
            self.search_history_df = pd.read_pickle(os.path.join(self.model_path, 'search_history.pkl'))
            self.users_df = pd.read_pickle(os.path.join(self.model_path, 'users.pkl'))
            return True
        except FileNotFoundError:
            print("Model files not found. Please train the model first.")
            return False
    
    def match_property_with_searches(self, property_data: Dict[str, Any], min_similarity: float = 0.2) -> List[Dict[str, Any]]:
        """
        Match a newly created property with user search history.
        
        Args:
            property_data: Dictionary containing property information
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of users to notify with relevance scores
        """
        # Ensure we have all necessary data
        if self.search_history_df is None or self.users_df is None:
            # If data is not loaded, try loading from files
            try:
                self.search_history_df = pd.read_pickle(os.path.join(self.model_path, 'search_history.pkl'))
                self.users_df = pd.read_pickle(os.path.join(self.model_path, 'users.pkl'))
                self.tfidf_vectorizer = joblib.load(os.path.join(self.model_path, 'tfidf_vectorizer.pkl'))
            except FileNotFoundError:
                return []
        
        # Create property text feature
        property_text = f"{property_data.get('name', '')} {property_data.get('city', '')}"
        # Ensure property text is not empty
        if not property_text.strip():
            property_text = "default_token"
        
        try:
            # Transform using the vectorizer
            property_vector = self.tfidf_vectorizer.transform([property_text])
            search_vectors = self.tfidf_vectorizer.transform(self.search_history_df['text_features'].values)
        except Exception as e:
            print(f"Error in vectorizer transform: {e}")
            # Return empty list if transformation fails
            return []
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(property_vector, search_vectors).flatten()
        
        # Create a DataFrame with search IDs and similarity scores
        matches_df = pd.DataFrame({
            'search_id': self.search_history_df['id'],
            'user_id': self.search_history_df['user_id'],
            'similarity_score': similarity_scores
        })
        
        # Filter by minimum similarity and price range
        filtered_matches = matches_df[
            (matches_df['similarity_score'] >= min_similarity) &
            (self.search_history_df['monthly_rent_gt'] <= property_data.get('monthly_rent', 0)) &
            (self.search_history_df['monthly_rent_lt'] >= property_data.get('monthly_rent', 0))
        ]
        
        # Group by user_id and take the maximum similarity score for each user
        user_matches = filtered_matches.groupby('user_id').agg({
            'similarity_score': 'max'
        }).reset_index()
        
        # Join with users DataFrame to get user details
        if not self.users_df.empty and not user_matches.empty:
            user_matches = user_matches.merge(self.users_df, left_on='user_id', right_on='id', how='inner')
        
        # Convert to list of dictionaries for notification
        notification_list = user_matches.to_dict(orient='records')
        
        return notification_list
    
    def match_unit_with_searches(self, unit_data: Dict[str, Any], property_data: Dict[str, Any], 
                                min_similarity: float = 0.2) -> List[Dict[str, Any]]:
        """
        Match a newly created unit with user search history.
        
        Args:
            unit_data: Dictionary containing unit information
            property_data: Dictionary containing parent property information
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of users to notify with relevance scores
        """
        if not self.load_model():
            return []
        
        # Create unit text feature by combining unit and property information
        unit_text = f"{unit_data.get('name', '')} {property_data.get('name', '')} {property_data.get('city', '')}"
        
        # Transform using the vectorizer
        unit_vector = self.tfidf_vectorizer.transform([unit_text])
        search_vectors = self.tfidf_vectorizer.transform(self.search_history_df['text_features'].values)
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(unit_vector, search_vectors).flatten()
        
        # Create a DataFrame with search IDs and similarity scores
        matches_df = pd.DataFrame({
            'search_id': self.search_history_df['id'],
            'user_id': self.search_history_df['user_id'],
            'similarity_score': similarity_scores
        })
        
        # Filter by minimum similarity and price range
        filtered_matches = matches_df[
            (matches_df['similarity_score'] >= min_similarity) &
            (self.search_history_df['monthly_rent_gt'] <= unit_data.get('monthly_rent', 0)) &
            (self.search_history_df['monthly_rent_lt'] >= unit_data.get('monthly_rent', 0))
        ]
        
        # Group by user_id and take the maximum similarity score for each user
        user_matches = filtered_matches.groupby('user_id').agg({
            'similarity_score': 'max'
        }).reset_index()
        
        # Join with users DataFrame to get user details
        if not self.users_df.empty and not user_matches.empty:
            user_matches = user_matches.merge(self.users_df, left_on='user_id', right_on='id', how='inner')
        
        # Convert to list of dictionaries for notification
        notification_list = user_matches.to_dict(orient='records')
        
        return notification_list
