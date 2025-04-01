from . import db, datetime, JSON

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='created')  # created, in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Keywords
    include_keywords = db.Column(JSON, default=list)
    exclude_keywords = db.Column(JSON, default=list)
    
    # Training config
    training_iterations = db.Column(db.Integer, default=0)
    current_iteration = db.Column(db.Integer, default=0)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='projects')
    citations = db.relationship('Citation', back_populates='project', cascade='all, delete-orphan')
    training_iterations = db.relationship('TrainingIteration', back_populates='project', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.name}>'