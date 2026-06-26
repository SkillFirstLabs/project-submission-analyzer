# AI Project Evaluation & Skill Matcher API

This system evaluates student project submissions by parsing zipped codebases, mapping code constructs to a local skill catalog, and producing structured mentor reports and interview questions using a configurable LLM provider.

## Design Choices & Architecture Walkthrough

### Pipeline Architecture
The project evaluation uses a pipeline architecture consisting of modular stages:
1. **Safe ZIP Extraction:** The ZIP is checked for path traversal attacks (`../../` sequences attempting to overwrite files outside the extraction root) and extracted safely. If it contains no files or is invalid, the request is rejected immediately with a `400 Bad Request` code.
2. **Lightweight Ranking:** Scans all files in the project, ranks files based on heuristics (extension, directory importance, size, file name like `main.py` or `Dockerfile`), and selects the top 30 files for contents loading.
3. **Loader:** Reads the first 500 lines or up to 100 KB of each selected file.
4. **Deep Ranking:** Analyzes file content for frameworks, authentication patterns, database setups, and OOP structures to rank the selected files. It takes the top 15 files to build a compact, high-quality prompt context for the LLM.
5. **Context Builder:** Combines project outcomes, project metadata, and the deeply ranked code snippets into a structured JSON payload for the LLM.
6. **LLM Service:** Queries the configured provider (`gemini`, `anthropic`, `openai`, or `groq`) and normalizes the JSON response into the required validation schema.

### Skill Catalog Integration & Caching Strategy
- The application relies on a local catalog stored in `catalog/skills.json` (no external database queries).
- During assessment, the LLM maps codebase technologies to skills in the catalog.
- **Dynamic Catalog Expansion:** If the codebase utilizes a clear skill not present in the catalog, the LLM proposes it. The application detects this proposal, generates a sequential ID (e.g. `sk-051`), and appends the new skill directly to `catalog/skills.json` at runtime, keeping it up to date.

### Security & Path Traversal Prevention
Extracting files from untrusted zip files is a common vulnerability vector (Zip Slip). To prevent path traversal:
- The service resolves the canonical absolute path of each destination file.
- It ensures that the absolute target path resides strictly within the canonical path of the extraction directory.
- It rejects extraction and raises a `ValueError` if a file path tries to escape.

---

## Folder Structure

```
.
├── app/
│   ├── api/
│   │   └── analyze.py          # /analyze-submission endpoint
│   ├── exceptions/
│   │   └── handlers.py         # Global exception handlers
│   ├── models/
│   │   ├── project_context.py  # Shared context
│   │   ├── project_file.py     # File metadata
│   │   ├── request_models.py   # Validation schemas
│   │   └── response_models.py  # Response schemas
│   ├── prompts/
│   │   ├── evaluation_prompt.txt
│   │   └── skills_prompt.txt
│   ├── services/
│   │   ├── zip_service.py      # Safe zip extraction
│   │   ├── scanner_service.py  # File directory scanner
│   │   ├── lightweight_ranking_service.py
│   │   ├── loader_service.py
│   │   ├── deep_ranking_service.py
│   │   ├── context_builder_service.py
│   │   └── llm_service.py   # LLM API client
│   └── main.py                 # FastAPI application setup
├── catalog/
│   └── skills.json             # Skill catalog JSON
├── extracted_projects/         # Target for extracted ZIP files (auto-created)
├── tests/
│   ├── test_zip_service.py     # Unit tests for ZIP service
│   └── test_analyze_api.py     # Integration tests for FastAPI endpoints
├── uploads/                    # Target for uploaded ZIP files (auto-created)
├── .env.example                # Config template
├── requirements.txt            # Dependency list
└── run.py                      # Server runner script
```

---

## Setup & Running the Server

### 1. Installation
Ensure you have Python 3.11+ installed. Clone the repository and set up a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows Powershell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in the API key for your chosen provider:
```bash
cp .env.example .env
```
Inside `.env`:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.0-flash

# Or use Groq
# LLM_PROVIDER=groq
# GROQ_API_KEY=YOUR_GROQ_API_KEY
# GROQ_MODEL=llama-3.3-70b-versatile
DEBUG=True
```

### 3. Start the Server
Start the development server:
```bash
python run.py
```
The server will start at `http://127.0.0.1:8000`. The interactive Swagger API documentation is available at `http://127.0.0.1:8000/docs`.

---

## Running Tests
Run all unit and integration tests using `pytest`:
```bash
pytest -v
```

---

## Example API Call

You can test the endpoint using `curl`:
```bash
curl -X POST "http://127.0.0.1:8000/analyze-submission" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "project_title=Inventory Management API" \
  -F "project_description=A Python FastAPI project managing inventory levels." \
  -F "project_outcomes=Build a REST API for inventory management
Implement user authentication and secure API
Deploy the application using Docker
Apply database design and normalization principles" \
  -F "questions_per_skill=2" \
  -F "zip_file=@sample_project.zip"
```

You can also submit multiple outcomes as repeated form fields:
```bash
curl -X POST "http://127.0.0.1:8000/analyze-submission" \
  -F "project_title=Inventory Management API" \
  -F "project_outcomes=Build a REST API for inventory management" \
  -F "project_outcomes=Implement user authentication and secure API" \
  -F "project_outcomes=Deploy the application using Docker" \
  -F "questions_per_skill=2" \
  -F "zip_file=@sample_project.zip"
```

### Response Format (JSON)
```json
{
  "project_title": "Inventory Management API",
  "project_summary": {
    "project_purpose": "Inventory Management API",
    "domain": "A Python FastAPI project managing inventory levels.",
    "technologies_used": ["Python", "FastAPI", "JWT"],
    "complexity": "Low to Medium",
    "key_features": ["Build a REST API for inventory management"],
    "architecture_style": "Layered Architecture"
  },
  "suggested_skills": [
    {
      "skill_id": "sk-001",
      "skill_name": "Python",
      "confidence": 0.95,
      "rationale": "Uses Python in main.py and api/routes/inventory.py",
      "proof_examples": [
        "main.py: contains Python FastAPI application setup",
        "api/routes/inventory.py: defines Python route handlers"
      ]
    },
    {
      "skill_id": "sk-018",
      "skill_name": "FastAPI",
      "confidence": 0.9,
      "rationale": "Imports FastAPI and defines routing in main.py",
      "proof_examples": [
        "main.py: imports FastAPI",
        "api/routes/inventory.py: uses APIRouter for inventory endpoints"
      ]
    },
    {
      "skill_id": "sk-052",
      "skill_name": "JWT",
      "confidence": 0.88,
      "rationale": "Uses JWT authentication in the auth middleware.",
      "proof_examples": [
        "app/auth.py: imports jwt and decodes JWT tokens"
      ]
    }
  ],
  "evaluation_report": {
    "skills": [
      {
        "skill_name": "Python",
        "proof_examples": [
          "main.py: contains Python FastAPI application setup"
        ],
        "questions": [
          {
            "question_text": "What is Python list comprehension and how can it optimize loops?",
            "question_focus": "conceptual",
            "expected_key_points": ["readable syntax", "performance"]
          },
          {
            "question_text": "In api/routes/inventory.py, how does the get_inventory function handle database querying?",
            "question_focus": "codebase_specific",
            "expected_key_points": ["get_inventory", "api/routes/inventory.py"]
          }
        ]
      }
    ],
    "summary": {
      "overall_alignment": "strong",
      "alignment_score": 0.85,
      "narrative": "The project is well structured and conforms to the requested FastAPI patterns. Best practices for routing are followed.",
      "outcome_evaluation": [
        {
          "stated_outcome": "Build a REST API for inventory management",
          "status": "met",
          "evidence": "api/routes/inventory.py defines GET routes on /inventory",
          "gap": null
        }
      ],
      "strengths": [
        "Clean folder organization",
        "Proper separation of concerns"
      ],
      "gaps": [
        "Lacks unit tests"
      ]
    },
    "metadata": {
      "files_analyzed": 5,
      "extraction_time_ms": 12,
      "model_tokens_used": 1850
    }
  },
  "project_statistics": {
    "files_analyzed": 5,
    "dependencies_found": 3,
    "code_samples_used": 5
  },
  "processing_time_ms": 2500
}
```

---

## Demo Walkthrough Video
[Demo Video Walkthrough Link](https://www.youtube.com/watch?v=dQw4w9WgXcQ)
