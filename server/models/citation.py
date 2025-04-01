from . import db, datetime, JSON

class Citation(db.Model):
    __tablename__ = 'citations'

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100))  # Optional external identifier (PMID, DOI, etc.)
    title = db.Column(db.Text, nullable=False)
    abstract = db.Column(db.Text)
    authors = db.Column(db.Text)
    year = db.Column(db.Integer)
    journal = db.Column(db.String(255))
    
    # ML-related fields
    relevance_score = db.Column(db.Float, default=0.5)  # Score between 0-1
    is_relevant = db.Column(db.Boolean)  # User-selected relevance (null if not manually labeled)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Raw data from import
    raw_data = db.Column(JSON)
    
    # Relationships
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    project = db.relationship('Project', back_populates='citations')
    
    # Many-to-many relationship with TrainingIteration
    training_selections = db.relationship('TrainingSelection', back_populates='citation')

    def __repr__(self):
        return f'<Citation {self.title[:30]}...>'

class TrainingIteration(db.Model):
    __tablename__ = 'training_iterations'

    id = db.Column(db.Integer, primary_key=True)
    iteration_number = db.Column(db.Integer, nullable=False)
    
    # Metrics
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    accuracy = db.Column(db.Float)
    
    # Additional metrics
    true_positives = db.Column(db.Integer)
    true_negatives = db.Column(db.Integer)
    false_positives = db.Column(db.Integer)
    false_negatives = db.Column(db.Integer)
    
    # Model parameters (optional)
    model_parameters = db.Column(JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    project = db.relationship('Project', back_populates='training_iterations')
    
    # Citations selected for this iteration
    selections = db.relationship('TrainingSelection', back_populates='iteration', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<TrainingIteration {self.iteration_number} for Project {self.project_id}>'

class TrainingSelection(db.Model):
    __tablename__ = 'training_selections'

    id = db.Column(db.Integer, primary_key=True)
    is_relevant = db.Column(db.Boolean, nullable=False)  # True for relevant, False for irrelevant
    
    # Foreign keys
    iteration_id = db.Column(db.Integer, db.ForeignKey('training_iterations.id'), nullable=False)
    citation_id = db.Column(db.Integer, db.ForeignKey('citations.id'), nullable=False)
    
    # Relationships
    iteration = db.relationship('TrainingIteration', back_populates='selections')
    citation = db.relationship('Citation', back_populates='training_selections')

    def __repr__(self):
        return f'<TrainingSelection citation={self.citation_id} is_relevant={self.is_relevant}>'