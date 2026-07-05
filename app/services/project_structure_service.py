import os


IMPORTANT_FILES = [
    "README.md",
    "requirements.txt",
    ".gitignore",
]


IMPORTANT_FOLDERS = [
    "app",
    "src",
    "static",
    "templates",
    "tests",
]


def analyze_project_structure(project_path: str):
    """
    Analyze the uploaded project structure.
    """

    files_found = []
    folders_found = []

    all_files = 0
    all_folders = 0

    for root, dirs, files in os.walk(project_path):
        all_folders += len(dirs)
        all_files += len(files)

        for file in files:
            if file in IMPORTANT_FILES:
                files_found.append(file)

        for folder in dirs:
            if folder in IMPORTANT_FOLDERS:
                folders_found.append(folder)

    score = 0

    score += len(files_found) * 5
    score += len(folders_found) * 5

    score = min(score, 30)

    return {
        "important_files": files_found,
        "important_folders": folders_found,
        "total_files": all_files,
        "total_folders": all_folders,
        "structure_score": score
    }