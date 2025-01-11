from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

# Import routes after app is created
from nosuai.apps.routes.github import *

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)