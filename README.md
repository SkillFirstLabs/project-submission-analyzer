# AI Project Submission Analyzer

## Overview

Analyzes uploaded software projects and provides:
- AI feedback
- Skill detection
- Framework detection
- README analysis
- Project structure analysis
- Code quality analysis
- Overall project score

## Tech Stack

- FastAPI
- Python
- Google Gemini API

## How to Run

pip install -r requirements.txt

uvicorn app.main:app --reload

## API

POST /analyze-submission

Upload a ZIP file to analyze a project.