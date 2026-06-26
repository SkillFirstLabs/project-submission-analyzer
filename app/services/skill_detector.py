import json
import re
from pathlib import Path
from typing import List, Dict, Any, Set
from app.config import settings
from app.models.schemas import SuggestedSkill

class SkillDetector:
    def __init__(self, skill_catalog_path: Path = settings.SKILL_CATALOG_PATH):
        self.catalog = self._load_catalog(skill_catalog_path)

    def _load_catalog(self, path: Path) -> List[Dict[str, Any]]:
        """Loads and validates the skill catalog JSON file."""
        if not path.exists():
            raise ValueError(f"Skill catalog file does not exist at: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Catalog must be a JSON array/list.")
                # Verify required structure
                for item in data:
                    if "skill_id" not in item or "skill_name" not in item:
                        raise ValueError("Each catalog item must have 'skill_id' and 'skill_name'.")
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid catalog JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to load catalog: {str(e)}")

    def _parse_requirements(self, content: str) -> Set[str]:
        """Parses requirements.txt for dependency names."""
        deps = set()
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Extract package name (matches alphabetic/numeric characters, hyphens, and underscores)
            match = re.match(r"^([a-zA-Z0-9_\-]+)", line)
            if match:
                deps.add(match.group(1).lower())
        return deps

    def _parse_package_json(self, content: str) -> Set[str]:
        """Parses package.json for dependencies."""
        deps = set()
        try:
            data = json.loads(content)
            for key in ("dependencies", "devDependencies"):
                if key in data and isinstance(data[key], dict):
                    for dep in data[key].keys():
                        deps.add(dep.lower())
        except Exception:
            pass
        return deps

    def _parse_pom_xml(self, content: str) -> Set[str]:
        """Parses pom.xml for maven artifact IDs."""
        deps = set()
        matches = re.findall(r"<artifactId>(.*?)</artifactId>", content)
        for m in matches:
            deps.add(m.strip().lower())
        return deps

    def _parse_gradle(self, content: str) -> Set[str]:
        """Parses build.gradle for dependencies."""
        deps = set()
        # Look for dependencies in single/double quotes
        matches = re.findall(r"['\"]([^'\"]+:[^'\"]+)['\"]", content)
        for m in matches:
            parts = m.split(":")
            if len(parts) >= 2:
                deps.add(parts[0].lower())  # Group ID
                deps.add(parts[1].lower())  # Artifact ID
        return deps

    def detect_skills(self, temp_dir: Path, extracted_files: List[Path]) -> List[SuggestedSkill]:
        """
        Scans extracted project files to detect skills from the catalog.
        """
        # Step 1: Parse configuration/manifest files for dependencies
        project_dependencies: Set[str] = set()
        
        for file_path in extracted_files:
            if not file_path.exists():
                continue
            
            name = file_path.name
            # Read small config files completely
            if name in ("requirements.txt", "package.json", "pom.xml", "build.gradle"):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if name == "requirements.txt":
                        project_dependencies.update(self._parse_requirements(content))
                    elif name == "package.json":
                        project_dependencies.update(self._parse_package_json(content))
                    elif name == "pom.xml":
                        project_dependencies.update(self._parse_pom_xml(content))
                    elif name == "build.gradle":
                        project_dependencies.update(self._parse_gradle(content))
                except Exception:
                    pass

        # Step 2: Scan source files for imports and code patterns
        detected_skills: List[SuggestedSkill] = []

        for skill in self.catalog:
            skill_id = skill["skill_id"]
            skill_name = skill["skill_name"]
            
            # Catalog criteria
            file_patterns = skill.get("file_patterns", [])
            catalog_imports = skill.get("imports", [])
            catalog_deps = skill.get("dependencies", [])
            catalog_code_patterns = skill.get("code_patterns", [])

            # Matches tracker
            matched_deps: Set[str] = set()
            matched_imports: Set[str] = set()
            matched_patterns: Set[str] = set()
            
            import_files: Set[str] = set()
            pattern_files: Set[str] = set()
            filename_only_matches: Set[str] = set()

            # Check dependencies
            for dep in catalog_deps:
                if dep.lower() in project_dependencies:
                    matched_deps.add(dep)

            # Check files and contents
            for file_path in extracted_files:
                if not file_path.exists():
                    continue
                
                rel_path_str = str(file_path.relative_to(temp_dir)).replace("\\", "/")
                
                # Check filename patterns
                file_matched = False
                for pattern in file_patterns:
                    if re.search(pattern, file_path.name, re.IGNORECASE):
                        file_matched = True
                        break
                
                if file_matched:
                    # For configuration skills like Docker, file presence is direct evidence
                    if skill_id in ("docker",):
                        filename_only_matches.add(file_path.name)
                        
                    # Read content for source analysis
                    # Avoid reading huge files, cap to settings.MAX_FILE_READ_SIZE_BYTES
                    if file_path.stat().st_size <= settings.MAX_FILE_READ_SIZE_BYTES:
                        try:
                            content = file_path.read_text(encoding="utf-8", errors="ignore")
                            
                            # Check imports
                            for imp in catalog_imports:
                                # Look for imports in code: e.g. import ... or require(...)
                                if re.search(r"\b" + re.escape(imp) + r"\b", content, re.IGNORECASE):
                                    matched_imports.add(imp)
                                    import_files.add(rel_path_str)
                                    
                            # Check code patterns
                            for pat in catalog_code_patterns:
                                if re.search(pat, content):
                                    matched_patterns.add(pat)
                                    pattern_files.add(rel_path_str)
                        except Exception:
                            pass

            # Step 3: Compute confidence score and rationale
            confidence = 0.0
            reasons = []

            # Dependency match is strongest (0.95)
            if matched_deps:
                confidence = max(confidence, 0.95)
                reasons.append(f"dependency declaration(s) '{', '.join(matched_deps)}'")

            # Import match is strong (0.90)
            if matched_imports:
                confidence = max(confidence, 0.90)
                reasons.append(f"import(s) '{', '.join(matched_imports)}' in source files")

            # Code pattern match is moderate to strong (0.85)
            if matched_patterns:
                confidence = max(confidence, 0.85)
                reasons.append(f"matching code patterns in {len(pattern_files)} file(s)")

            # Config files / docker rules
            if filename_only_matches:
                confidence = max(confidence, 0.95)
                reasons.append(f"configuration file(s) '{', '.join(filename_only_matches)}'")

            # Boost confidence slightly if we have multiple indicators
            if len(reasons) > 1:
                confidence = min(0.98, confidence + 0.03)

            # Only suggest if we have concrete evidence (confidence > 0)
            if confidence > 0.0:
                # Format a clean rationale string
                if reasons:
                    rationale = f"Detected from {', '.join(reasons)}."
                else:
                    rationale = "Detected from project file matching patterns."
                
                detected_skills.append(
                    SuggestedSkill(
                        skill_id=skill_id,
                        skill_name=skill_name,
                        confidence=round(confidence, 2),
                        rationale=rationale
                    )
                )

        return detected_skills
