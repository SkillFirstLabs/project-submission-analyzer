# Safe ZIP extraction
import zipfile
import uuid
from pathlib import Path

EXTRACT_DIR = Path("temp/extracted")
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)


def extract_zip(zip_path: Path) -> Path:

    extraction_folder = EXTRACT_DIR / str(uuid.uuid4())
    extraction_folder.mkdir(parents=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:

        for member in zip_ref.namelist():

            member_path = extraction_folder / member

            if not str(member_path.resolve()).startswith(
                str(extraction_folder.resolve())
            ):
                raise Exception("Unsafe ZIP detected")

        zip_ref.extractall(extraction_folder)

    return extraction_folder