import pytest
from app.services.outcome_evaluator import _parse_eval_response

def test_parse_eval_response_normal():
    raw_json = """
    {
      "strengths": ["Excellent use of FastAPI", "Good code structure"],
      "gaps": ["Missing tests for database"],
      "summary": "This is a good project.",
      "outcome_evaluations": [
        {
          "stated_outcome": "implement fast api",
          "is_met": true,
          "confidence": 0.9,
          "evidence": "main.py",
          "gaps": []
        }
      ]
    }
    """
    res = _parse_eval_response(raw_json)
    assert res is not None
    assert res["strengths"] == ["Excellent use of FastAPI", "Good code structure"]
    assert res["gaps"] == ["Missing tests for database"]

def test_parse_eval_response_capitalized():
    raw_json = """
    {
      "Strengths": ["Excellent use of FastAPI"],
      "Gaps": ["Missing tests"],
      "summary": "This is a good project.",
      "outcome_evaluations": []
    }
    """
    res = _parse_eval_response(raw_json)
    assert res is not None
    assert res["strengths"] == ["Excellent use of FastAPI"]
    assert res["gaps"] == ["Missing tests"]

def test_parse_eval_response_with_markdown():
    raw_json = """
    Here is the response:
    ```json
    {
      "strengths": ["Excellent use of FastAPI"],
      "gaps": ["Missing tests"],
      "summary": "This is a good project.",
      "outcome_evaluations": []
    }
    ```
    """
    res = _parse_eval_response(raw_json)
    assert res is not None
    assert res["strengths"] == ["Excellent use of FastAPI"]
    assert res["gaps"] == ["Missing tests"]


def test_detailed_fallback_eval_clean():
    from app.services.outcome_evaluator import _detailed_fallback_eval
    file_contents = {
        "main.py": "def add(a, b): return a + b",
        "test_main.py": "from main import add\ndef test_add(): assert add(1, 2) == 3",
        "requirements.txt": "pytest==8.0.0"
    }
    outcomes = "implement add function"
    report = _detailed_fallback_eval(outcomes, file_contents)
    
    assert report is not None
    assert any("Security: No high-severity" in s for s in report.strengths)
    assert any("Testing: Automated tests" in s for s in report.strengths)
    assert any("Configuration: Standard dependency" in s for s in report.strengths)
    assert any("LLM offline" in g for g in report.gaps)
    assert not any("No automated unit tests" in g for g in report.gaps)
    assert not any("Missing standard dependency" in g for g in report.gaps)


def test_detailed_fallback_eval_vulnerabilities():
    from app.services.outcome_evaluator import _detailed_fallback_eval
    file_contents = {
        "main.py": "eval(input('Enter code:'))",
    }
    outcomes = "run user input"
    report = _detailed_fallback_eval(outcomes, file_contents)
    
    assert report is not None
    assert any("Security: High-severity issue" in g for g in report.gaps)
    assert any("Testing: No automated unit tests" in g for g in report.gaps)
    assert any("Configuration: Missing standard dependency" in g for g in report.gaps)

