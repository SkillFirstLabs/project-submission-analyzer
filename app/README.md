# Project Submission AI Analyzer

This FastAPI application analyzes an uploaded project ZIP file and generates interview questions based on detected skills.

## Features

- Upload a project ZIP file
- Detect technologies used in the project
- Suggest only skills that exist in the built-in catalog
- Attach a confidence score and rationale to every suggested skill
- Generate technical interview questions for each detected skill
- Serve a simple browser UI and a JSON API

## Quick start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the server from the workspace root:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. Open http://127.0.0.1:8000/ in your browser.

## Environment variables

The app does not require any external API keys for the local demo mode.

## Folder structure

```text
app/                # FastAPI app and analysis logic
uploads/            # uploaded ZIPs
extracted_projects/ # extracted demo submissions
sample_submissions/ # sample ZIP sources and demo archive
tests/              # regression tests
```

## Running tests

```bash
pytest -q
```

## Example API call

```bash
curl -X POST http://127.0.0.1:8000/analyze-submission \
  -F "project_title=FastAPI CRUD App" \
  -F "project_description=A small CRUD app" \
  -F "project_outcomes=Create, read, update, and delete items using REST endpoints." \
  -F "questions_per_skill=2" \
  -F "zip_file=@sample_submissions/fastapi_crud.zip"
```

## Demo

Demo ZIP: [sample_submissions/fastapi_crud.zip](sample_submissions/fastapi_crud.zip)


## Notes

- Interview questions are generated locally from skill templates and project context.
- The app ignores common folders such as `__pycache__`, `.git`, `venv`, and `node_modules` during file scanning.
- ZIP parsing now rejects unsafe path traversal entries.
