import os
import shutil
import uuid
import zipfile

from app.models.project_context import ProjectContext


class ZipService:
    """
    Handles ZIP extraction and updates the ProjectContext.
    """

    EXTRACT_ROOT = "extracted_projects"

    def __init__(self):
        os.makedirs(self.EXTRACT_ROOT, exist_ok=True)

    def process(
        self,
        context: ProjectContext
    ) -> ProjectContext:
        """
        Extract uploaded ZIP and update ProjectContext.
        """

        if not os.path.exists(context.zip_path):
            raise FileNotFoundError("Uploaded ZIP file not found.")

        if not zipfile.is_zipfile(context.zip_path):
            raise ValueError("Invalid ZIP file.")

        project_id = str(uuid.uuid4())

        extract_path = os.path.join(
            self.EXTRACT_ROOT,
            project_id
        )

        os.makedirs(extract_path, exist_ok=True)

        try:

            with zipfile.ZipFile(
                context.zip_path,
                "r"
            ) as zip_ref:

                namelist = zip_ref.namelist()
                if not namelist:
                    raise ValueError("The ZIP archive is empty.")

                resolved_extract_root = os.path.abspath(extract_path)
                
                has_files = False
                for member in zip_ref.infolist():
                    # Resolve destination path to verify it stays inside extract_path
                    target_path = os.path.abspath(os.path.join(resolved_extract_root, member.filename))
                    if not target_path.startswith(resolved_extract_root + os.sep) and target_path != resolved_extract_root:
                        raise ValueError(f"Path traversal attempt detected in ZIP: {member.filename}")
                    
                    if not member.is_dir():
                        has_files = True

                if not has_files:
                    raise ValueError("Empty project: No files found in the ZIP archive.")

                # Extract safely since all paths have been checked
                for member in zip_ref.infolist():
                    zip_ref.extract(member, resolved_extract_root)

                context.metadata["files_in_zip"] = len(namelist)

        except Exception as e:

            shutil.rmtree(
                extract_path,
                ignore_errors=True
            )
            if isinstance(e, ValueError):
                raise e
            raise ValueError(
                f"Failed to extract ZIP: {str(e)}"
            )

        context.project_id = project_id
        context.extract_path = extract_path

        return context