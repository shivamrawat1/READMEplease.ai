from app import app
from flask import render_template, request

@app.route("/wait")
def wait_screen():
    """Display wait screen with video."""
    is_https = request.is_secure
    return render_template('wait.html', is_https=is_https)