import os
import zipfile


# ==============================
# 1. SAFE FILE READING
# ==============================
def read_file_safely(file_path: str) -> str:
    """
    Safely read text file content.
    Prevents crashes on encoding errors.
    """

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f""


# ==============================
# 2. FILE TYPE CHECK
# ==============================
def is_code_file(filename: str) -> bool:
    """
    Filter only relevant code files.
    """

    code_extensions = [
        ".py", ".js", ".ts", ".java",
        ".cpp", ".c", ".go", ".rs",
        ".html", ".css", ".json"
    ]

    return any(filename.endswith(ext) for ext in code_extensions)


# ==============================
# 3. SAFE ZIP EXTRACTION CHECK
# ==============================
def is_safe_zip_path(base_path: str, target_path: str) -> bool:
    """
    Prevent ZIP path traversal attacks.
    Ensures files are extracted only inside target directory.
    """

    abs_base = os.path.abspath(base_path)
    abs_target = os.path.abspath(target_path)

    return abs_target.startswith(abs_base)


# ==============================
# 4. ZIP EXTRACTION SAFETY HELPER
# ==============================
def safe_extract_zip(zip_path: str, extract_to: str):
    """
    Safely extract ZIP files without path traversal risk.
    """

    with zipfile.ZipFile(zip_path, "r") as zip_ref:

        for member in zip_ref.namelist():
            member_path = os.path.join(extract_to, member)

            if not is_safe_zip_path(extract_to, member_path):
                raise Exception(f"Unsafe ZIP file detected: {member}")

        zip_ref.extractall(extract_to)


# ==============================
# 5. FILE SIZE CHECK
# ==============================
def get_file_size_kb(file_path: str) -> float:
    """
    Returns file size in KB.
    Useful for filtering large files before LLM.
    """

    try:
        size = os.path.getsize(file_path)
        return round(size / 1024, 2)
    except Exception:
        return 0.0