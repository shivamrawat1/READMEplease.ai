from flask import Flask
from .routes.video_to_audio import video_to_audio_blueprint

def create_app():
    app = Flask(__name__)
    # Register blueprint with a URL prefix
    app.register_blueprint(video_to_audio_blueprint, url_prefix='')
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
