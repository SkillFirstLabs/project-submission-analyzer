from pathlib import Path

from services import gemini_service


def test_get_api_key_reads_project_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=test-key-from-env\n", encoding="utf-8")

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    assert gemini_service.get_api_key(env_file) == "test-key-from-env"


def test_get_api_key_falls_back_to_google_key(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GOOGLE_API_KEY=test-key-from-google\n", encoding="utf-8")

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    assert gemini_service.get_api_key(env_file) == "test-key-from-google"


def test_get_api_key_prefers_project_env_over_existing_environment(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_API_KEY=env-file-key\n", encoding="utf-8")

    monkeypatch.setenv("GEMINI_API_KEY", "existing-env-key")

    assert gemini_service.get_api_key(env_file) == "env-file-key"


def test_get_model_name_defaults_to_supported_flash(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")

    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GOOGLE_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_MODEL_NAME", raising=False)

    assert gemini_service.get_model_name(env_file) == "gemini-2.0-flash"


def test_get_model_name_reads_env_override(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GEMINI_MODEL=gemini-2.5-flash\n", encoding="utf-8")

    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GOOGLE_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_MODEL_NAME", raising=False)

    assert gemini_service.get_model_name(env_file) == "gemini-2.5-flash"
