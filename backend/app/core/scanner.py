import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any

class CodebaseScanner:
    """
    Scans an extracted codebase directory to identify tech stack elements,
    dependencies, import graphs, database configs, and architectural components.
    """
    
    # Common extension to language mapping
    LANGUAGE_MAP = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'React JS',
        '.ts': 'TypeScript',
        '.tsx': 'React TS',
        '.html': 'HTML',
        '.css': 'CSS',
        '.sh': 'Shell Script',
        '.yml': 'YAML',
        '.yaml': 'YAML',
        '.json': 'JSON',
        '.md': 'Markdown',
        '.sql': 'SQL',
        '.dockerfile': 'Dockerfile'
    }

    @classmethod
    def scan_project(cls, root_dir: Path) -> Dict[str, Any]:
        resolved_root = root_dir.resolve()
        
        file_tree: List[str] = []
        languages_count: Dict[str, int] = {}
        dependencies: List[Dict[str, str]] = []
        detected_techs: Set[str] = set()
        configs: List[str] = []
        routes: List[str] = []
        has_docker = False
        has_auth = False
        has_db = False
        has_testing = False

        # Compile file tree and count languages
        for path in resolved_root.rglob('*'):
            # Skip hidden folders like .git or node_modules
            if any(part.startswith('.') or part in ['node_modules', '__pycache__', 'dist', 'build'] for part in path.parts):
                continue
                
            relative_path = path.relative_to(resolved_root).as_posix()
            
            if path.is_file():
                file_tree.append(relative_path)
                
                # Language detection
                ext = path.suffix.lower()
                lang = cls.LANGUAGE_MAP.get(ext)
                if not lang and path.name.lower() == 'dockerfile':
                    lang = 'Dockerfile'
                if lang:
                    languages_count[lang] = languages_count.get(lang, 0) + 1

                # Check configuration manifests
                if path.name == 'package.json':
                    dependencies.extend(cls._parse_package_json(path))
                    configs.append(relative_path)
                elif path.name in ['requirements.txt', 'Pipfile', 'pyproject.toml']:
                    dependencies.extend(cls._parse_requirements_txt(path))
                    configs.append(relative_path)
                elif path.name in ['docker-compose.yml', 'docker-compose.yaml', 'Dockerfile']:
                    has_docker = True
                    configs.append(relative_path)
                elif path.name.startswith('.env'):
                    configs.append(relative_path)

                # Scan file source contents for import markers
                if ext in ['.py', '.js', '.jsx', '.ts', '.tsx']:
                    file_findings = cls._scan_file_contents(path)
                    
                    if file_findings.get('has_auth'):
                        has_auth = True
                    if file_findings.get('has_db'):
                        has_db = True
                    if file_findings.get('has_testing'):
                        has_testing = True
                    
                    detected_techs.update(file_findings.get('techs', []))
                    routes.extend(file_findings.get('routes', []))

        # Summarize programming languages by percentage
        total_lang_files = sum(languages_count.values())
        lang_percentages = {}
        if total_lang_files > 0:
            lang_percentages = {
                lang: round((count / total_lang_files) * 100)
                for lang, count in languages_count.items()
            }

        return {
            "file_count": len(file_tree),
            "files_list": file_tree,
            "languages": lang_percentages,
            "dependencies": dependencies,
            "technologies": list(detected_techs),
            "config_files": configs,
            "api_routes": routes,
            "features": {
                "docker": has_docker,
                "authentication": has_auth,
                "database": has_db,
                "testing": has_testing
            }
        }

    @staticmethod
    def _parse_package_json(path: Path) -> List[Dict[str, str]]:
        deps = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Read regular and dev dependencies
                for dep_type in ['dependencies', 'devDependencies']:
                    if dep_type in data:
                        for name, version in data[dep_type].items():
                            deps.append({
                                "name": name,
                                "version": version,
                                "type": "Production" if dep_type == 'dependencies' else "Development"
                            })
        except Exception:
            pass
        return deps

    @staticmethod
    def _parse_requirements_txt(path: Path) -> List[Dict[str, str]]:
        deps = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Regex to parse package and version (e.g. fastapi==0.100.0 or numpy>=1.2.0)
                        match = re.match(r'^([a-zA-Z0-9_\-]+)\s*(?:[=><~]+.*)?$', line)
                        if match:
                            pkg_name = match.group(1)
                            version = line.replace(pkg_name, '').strip()
                            deps.append({
                                "name": pkg_name,
                                "version": version if version else "latest",
                                "type": "Production"
                            })
        except Exception:
            pass
        return deps

    @classmethod
    def _scan_file_contents(cls, path: Path) -> Dict[str, Any]:
        findings = {
            "techs": [],
            "routes": [],
            "has_auth": False,
            "has_db": False,
            "has_testing": False
        }
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Search keywords / technologies
            tech_regexes = {
                "Kafka": r'kafkajs|kafka-python|confluent_kafka',
                "Redis": r'redis|aioredis',
                "FastAPI": r'fastapi|APIRouter',
                "Express": r'express',
                "React": r'react|useState|useEffect',
                "PyTorch": r'torch|nn\.Module|CUDA',
                "NumPy": r'numpy|np\.',
                "PostgreSQL": r'pg|psycopg2|postgresql',
                "MongoDB": r'mongoose|pymongo|mongodb'
            }

            for tech, pattern in tech_regexes.items():
                if re.search(pattern, content, re.IGNORECASE):
                    findings["techs"].append(tech)

            # Search auth indicators
            if re.search(r'jwt|passport|oauth|bcrypt|auth0|login|register|password|session', content, re.IGNORECASE):
                findings["has_auth"] = True

            # Search database indicators
            if re.search(r'mongoose\.model|sequelize|prisma|sqlite3|create_engine|connect\(|db\.', content, re.IGNORECASE):
                findings["has_db"] = True

            # Search testing patterns
            if re.search(r'describe\(|test\(|it\(|pytest|unittest|assert', content, re.IGNORECASE):
                findings["has_testing"] = True

            # Search API route declarations
            # Express: app.get('/...', ...), router.post('/...', ...)
            express_matches = re.findall(r'(?:app|router)\.(get|post|put|delete)\(\s*[\'"]([^\'"]+)[\'"]', content)
            for method, route in express_matches:
                findings["routes"].append(f"{method.upper()} {route}")

            # FastAPI: @app.get("/..."), @router.post("/...")
            fastapi_matches = re.findall(r'@(?:app|router)\.(get|post|put|delete)\(\s*[\'"]([^\'"]+)[\'"]', content)
            for method, route in fastapi_matches:
                findings["routes"].append(f"{method.upper()} {route}")

        except Exception:
            pass

        return findings
