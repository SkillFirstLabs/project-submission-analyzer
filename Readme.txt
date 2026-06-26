# Project Submission AI Analyzer

## Overview

Project Submission AI Analyzer is a FastAPI-based application that analyzes a student's project submission 
provided as a ZIP file. The system extracts the project files, identifies relevant technical skills from a 
predefined skill catalog, generates interview questions for the detected skills, and produces an evaluation 
report for mentor-led viva assessments.

---

## Features

* Upload project ZIP files through a REST API.
* Safe extraction and analysis of project files.
* Automatic skill detection based on project contents.
* Confidence score and rationale for each detected skill.
* Automatic generation of conceptual and codebase-specific interview questions.
* Outcome evaluation and project summary generation.
* Returns a structured JSON response.

---

## Project Structure

project-submission-analyzer/

├── main.py

├── requirements.txt

├── skill_catalog.json

├── uploads/

├── extracted/

└── utils/

  ├── zip_handler.py

  ├── skill_detector.py

  ├── question_generator.py

  └── outcome_evaluator.py

---

## Requirements

* Python 3.11+ (Tested on Python 3.13)
* FastAPI
* Uvicorn
* Python Multipart
* Python Dotenv
* Pydantic

---

## Installation

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run the Server

```bash
python -m uvicorn main:app --reload
```

### Step 3: Open Swagger Documentation

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoint

### POST /analyze-submission

#### Input Parameters

| Parameter           | Type    | Required |
| ------------------- | ------- | -------- |
| project_title       | String  | Yes      |
| project_description | String  | No       |
| project_outcomes    | String  | Yes      |
| questions_per_skill | Integer | No       |
| zip_file            | File    | Yes      |

---

## Sample Input

Project Title:
Student Management System

Project Outcomes:

* Build CRUD operations
* Use Python
* Store data

ZIP File:
sample_project.zip

---

## Sample Output

```json
{
  "project_title": "sample",
  "suggested_skills": [
    {
      "skill_id": "sk-001",
      "skill_name": "Python",
      "confidence": 0.9,
      "rationale": "Python files found."
    }
  ],
  "evaluation_report": {
    "skills": [
      {
        "skill_name": "Python",
        "questions": [
          {
            "question_text": "What is Python and why is it used?",
            "question_focus": "conceptual"
          }
        ]
      }
    ]
  }
}
```

---

## Technologies Used

* Python
* FastAPI
* Uvicorn
* JSON
* File Handling
* ZIP Processing

---

## Future Enhancements

* Integration with LLM APIs for intelligent question generation.
* Advanced code analysis and dependency detection.
* Improved outcome evaluation with evidence extraction.
* Support for additional programming languages and frameworks.

---

