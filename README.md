# ProctorAI - Project Submission Analyzer

AI-powered tool that analyzes student project submissions, generates interview questions, and conducts proctored live viva sessions.

## Quick Start

### 1. Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### 2. Run the Server

```bash
uvicorn app.main:app --reload --port 8080
```

Open your browser: **http://localhost:8080**

### 3. Test API Connection

Visit: **http://localhost:8080/api-status**

This checks if your API key is working properly.

## Features

- 📦 **ZIP Analysis**: Upload project ZIP files for automated code analysis
- 🧠 **AI Skill Detection**: Identifies skills demonstrated in the codebase
- 📝 **Question Generation**: Creates relevant interview questions
- 🎥 **Live Proctoring**: Webcam-based integrity monitoring during viva
- 📊 **Combined Reports**: Detailed evaluation with proctoring metrics

## API Endpoints

- `GET /` - Web interface
- `GET /health` - Server health check
- `GET /api-status` - API connection test
- `POST /analyze-submission` - Upload and analyze project ZIP
- `POST /viva-session/start` - Start proctored session
- `POST /viva-session/event` - Record proctoring events
- `POST /viva-session/end` - End session and get final report

## Project Structure

```
app/
  ├── main.py           # API routes
  ├── config.py         # Configuration settings
  ├── llm_client.py     # OpenRouter API client
  ├── schemas.py        # Data models
  ├── skill_engine.py   # AI skill analysis
  ├── zip_analyzer.py   # ZIP extraction & analysis
  └── proctoring.py     # Session management

static/
  ├── index.html        # Web UI
  ├── app.js            # Frontend logic
  └── style.css         # Styling

data/end the 
  └── skill_catalog.json # Skills database

tests/
  ├── test_proctoring.py
  └── test_zip_safety.py
```

## Configuration

All settings are in `.env`:

- `OPENROUTER_API_KEY` - Your API key
- `OPENROUTER_MODEL` - AI model to use
- `MAX_ZIP_SIZE_MB` - Max upload size
- `GAZE_OFF_LOW_S` - Proctoring threshold
- And more...

See `.env.example` for all options.

## Running Tests

```bash
pytest tests/ -v
```

## Privacy Note

Proctoring runs client-side in the browser. No video/audio is uploaded. Only event metadata (timestamps, durations) is sent to the server.
