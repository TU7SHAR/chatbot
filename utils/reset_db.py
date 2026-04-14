import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from models.models import db

with app.app_context():
    print("Dropping old tables...")
    db.drop_all()
    
    print("Building new Enterprise schema...")
    db.create_all()
    
    print("Database reset complete! You can now start the app.")