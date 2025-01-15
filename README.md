
# READMEplease.ai - Markdown Generator with Embedded Text and Screenshots

A Flask web application that generates Markdown documents by processing videos or GitHub repositories as input. The application transcribes speech using OpenAI Whisper, extracts screenshots at moments when specific keywords are spoken, and embeds both the text and screenshots into the Markdown document for seamless documentation.

[![Python](https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=Python&logoColor=white)](https://www.python.org/)
[![HTML](https://img.shields.io/badge/HTML-gray.svg?style=for-the-badge&logo=HTML&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![Procfile](https://img.shields.io/badge/Procfile-gray.svg?style=for-the-badge&logo=Procfile&logoColor=white)](https://devcenter.heroku.com/articles/procfile)

---

Demo Video: [https://youtu.be/xHDUDiyhM9k](https://youtu.be/xHDUDiyhM9k)

## 🔗 Table of Contents

1. [📍 Overview](#-overview)
2. [👾 Features](#-features)
3. [📁 Project Structure](#-project-structure)
4. [🚀 Getting Started](#-getting-started)
5. [📌 Roadmap](#-roadmap)
6. [🙌 Acknowledgments](#-acknowledgments)

---

## 📍 Overview

NosuAI provides an efficient solution for generating Markdown documentation. Whether you input a GitHub repository or a video file, NosuAI processes the content to create a Markdown document enriched with text and embedded screenshots. It's ideal for developers, researchers, and content creators looking to automate documentation tasks.

---

## 👾 Features

- **Markdown Generation**: Automatically generates Markdown documents with transcriptions and embedded screenshots.
- **Input Options**:
  - Process GitHub repositories to extract README data and embedded elements.
  - Process video files to extract audio, transcribe content, and capture screenshots based on keywords.
- **Speech Transcription**: Utilize OpenAI Whisper for accurate transcription.
- **Screenshot Integration**: Generate and embed screenshots at moments when keywords are spoken.
- **Secure Development**: HTTPS support for local OAuth callbacks.
- **Debugging Tools**: Comprehensive logging for efficient troubleshooting.

---

## 📁 Project Structure

```plaintext
nosuai/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── runtime.txt            # Specifies Python version for deployment
├── Procfile               # Process declaration for Heroku
├── Aptfile                # Additional dependencies for deployment
├── .env.example           # Environment variable template
├── apps/
│   ├── routes/
│   │   ├── github_processing.py
│   │   ├── video_processing.py
│   │   ├── create_markdown.py
│   │   ├── github.py
│   │   ├── notion.py
│   │   └── transcription_with_timestamps.py
│   ├── static/
│   │   └── css/
│   ├── templates/
│   │   ├── upload.html
│   │   ├── github.html
│   │   └── notion.html
│   └── utils/
│       └── clean_samples.py
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- FFmpeg
- OpenCV
- OpenAI API Key
- (Optional) GitHub & Notion OAuth credentials

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/shivamrawat1/nosuai.git
   cd nosuai
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:

   ```env
   OPENAI_API_KEY=your-openai-api-key
   FLASK_SECRET_KEY=your-secret-key
   ```

5. Start the Flask application:

   ```bash
   python app.py
   ```

6. Open your browser at [https://127.0.0.1:5000](https://127.0.0.1:5000).

---

## 📌 Roadmap

- [x] Markdown generation from video inputs.
- [x] Transcription and screenshot embedding.
- [x] Full GitHub repository processing with enhanced README generation.
- [ ] Support for multilingual transcription.
- [ ] Enhanced UI for easier input selection and customization.

---


## 🙌 Acknowledgments

Special thanks to the OpenAI, Flask, and developer communities for their tools and resources.

--- 
