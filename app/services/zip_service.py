import zipfile
import shutil
from pathlib import Path

# Folder paths
UPLOAD_FOLDER = Path("uploads")
TEMP_FOLDER = Path("temp")

UPLOAD_FOLDER.mkdir(exist_ok=True)
TEMP_FOLDER.mkdir(exist_ok=True)

# Ignore these folders
IGNORE_FOLDERS = {
    "node_modules",
    ".git",
    "venv",
    "dist",
    "__pycache__"
}

# Read only these file types
VALID_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".java",
    ".html",
    ".css",
    ".json",
    ".md",
    ".txt"
}


def save_zip(uploaded_file):
    file_path = UPLOAD_FOLDER / uploaded_file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

    return file_path


def extract_zip(zip_path):
    if TEMP_FOLDER.exists():
        shutil.rmtree(TEMP_FOLDER)

    TEMP_FOLDER.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(TEMP_FOLDER)

    return TEMP_FOLDER


def read_project_files(project_folder):
    """
    Read all supported source files and combine them into one string.
    Returns:
        all_code -> string
        files_analyzed -> list
    """

    all_code = ""
    files_analyzed = []

    for file in project_folder.rglob("*"):

        # Ignore folders
        if any(part in IGNORE_FOLDERS for part in file.parts):
            continue

        # Ignore non-files
        if not file.is_file():
            continue

        # Ignore unsupported extensions
        if file.suffix.lower() not in VALID_EXTENSIONS:
            continue

        files_analyzed.append(str(file))

        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            all_code += f"\n\n===== {file} =====\n"
            all_code += content

        except Exception:
            pass

    return all_code, files_analyzed