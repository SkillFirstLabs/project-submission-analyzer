# Project Submission AI Analyzer

A FastAPI-based application that analyzes uploaded project submissions in ZIP format and generates a structured evaluation report. The system extracts the archive, inspects the project structure and source files, and uses a Groq-powered LLM to produce a project summary, relevant skills, interview-style questions, and basic statistics.

## Overview

This project is designed for evaluating student or candidate project submissions. A user uploads a ZIP archive containing a project, and the service returns a JSON report that can be used for review, scoring, or interview preparation.

The analyzer performs three main steps:

1. File and archive inspection
2. Evidence-based project analysis
3. LLM-generated skill and question generation

## Key Features

- Upload ZIP archives containing project source code
- Safe extraction of uploaded content
- Analysis of file tree, imports, dependencies, and code samples
- LLM-based project summary generation using Groq
- Skill matching based on visible evidence from the project
- Automatic generation of technical questions for each detected skill
- Structured JSON output for downstream integration

## Tech Stack

- Python
- FastAPI
- Uvicorn
- python-multipart
- Pydantic
- python-dotenv
- Groq SDK
- Gradio
- NetworkX
- Tiktoken
- Orjson

## Project Structure

```text
app/
  api/
    routes.py          # API endpoint for analysis
  models/
    schemas.py         # Data models
  prompts/
    project_prompt.py  # Prompt for project summary
    skill_prompt.py    # Prompt for skill matching
    question_prompt.py # Prompt for question generation
  services/
    llm_analyzer.py    # LLM integration and JSON parsing
    project_analyzer.py# File tree, imports, and dependency analysis
    report_builder.py   # Final report formatting
    zip_service.py      # Safe ZIP extraction
run.py                  # Startup script for the FastAPI server
requirements.txt        # Python dependencies
```

## Setup

1. Create and activate a virtual environment
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add your Groq API key
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

4. Start the server
   ```bash
   python run.py
   ```

The application will run at:

```text
http://127.0.0.1:8000
```

## API Usage

### Analyze a Project

Endpoint:

```http
POST /analyze
```

Request:
- Form-data
- Field name: `file`
- File type: ZIP archive

Example using curl:

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -F "file=@your_project.zip"
```

### Response Format

The response contains:

- `project_summary`: purpose, domain, technologies, complexity, features, and architecture
- `skills`: detected technical skills with evidence and confidence
- `questions`: generated conceptual and codebase-specific interview questions
- `project_statistics`: file count, dependency count, and code sample count

## Notes

- The service expects a valid ZIP file.
- Empty or non-code projects are handled gracefully and return a minimal report.
- Uploaded files and extracted project folders are stored under the `temp` directory.
- ZIP extraction includes safety checks to prevent path traversal issues.

## Running the App

You can also start the app directly with Uvicorn:

```bash
uvicorn app.main:app --reload
```

