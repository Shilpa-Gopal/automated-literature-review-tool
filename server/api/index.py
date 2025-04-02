import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your Flask app
from server.app import create_app

# Initialize the app
app = create_app()

# Vercel handler
def handler(request, context):
    return app(request, context)
