from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create Flask app with custom template folder
app = Flask(__name__, 
           template_folder='apps/templates',
           static_folder='apps/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

# Import routes after app is created
from apps.routes.github import *
from apps.routes.notion import *
from apps.routes.other import *
from apps.routes.video_to_audio import *

if __name__ == '__main__':
    app.run(debug=True, 
            host='127.0.0.1', 
            port=5000,
            ssl_context='adhoc', 
            host='127.0.0.1', 
            port=5000,
            ssl_context='adhoc')