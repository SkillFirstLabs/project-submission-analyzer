from typing import Dict, List, Any

class AuthenticityEngine:
    """
    Deterministic rule-based scoring engine that evaluates codebase properties.
    Calculates category scores, identifies missing items, and compiles evidence logs.
    """

    @classmethod
    def calculate_authenticity(cls, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        files_list = scan_results.get("files_list", [])
        dependencies = [d.get("name", "").lower() for d in scan_results.get("dependencies", [])]
        features = scan_results.get("features", {})
        languages = scan_results.get("languages", {})
        api_routes = scan_results.get("api_routes", [])
        config_files = [f.split("/")[-1] for f in scan_results.get("config_files", [])]

        # 1. Frontend Score
        fe_score = 20
        fe_langs = {"React JS", "React TS", "HTML", "CSS"}
        matched_fe_langs = [l for l in fe_langs if l in languages]
        fe_score += len(matched_fe_langs) * 15
        
        fe_libs = ["react", "tailwind", "bootstrap", "framer-motion", "recharts", "lucide-react", "vue", "angular", "svelte"]
        matched_fe_libs = [lib for lib in fe_libs if lib in dependencies]
        fe_score += len(matched_fe_libs) * 10
        fe_score = min(100, fe_score)

        # 2. Backend Score
        be_score = 20
        be_libs = ["express", "fastapi", "flask", "django", "rails", "spring", "nestjs", "uvicorn", "gunicorn", "nodemon"]
        matched_be_libs = [lib for lib in be_libs if lib in dependencies]
        be_score += len(matched_be_libs) * 20
        
        if len(api_routes) > 0:
            be_score += 20
        if len(api_routes) > 5:
            be_score += 10
            
        if any(l in languages for l in ["Python", "JavaScript", "TypeScript"]):
            be_score += 10
        be_score = min(100, be_score)

        # 3. Database Score
        db_score = 20
        if features.get("database"):
            db_score += 40
        db_libs = ["pg", "postgres", "mongoose", "mongodb", "redis", "mysql", "sqlite", "sqlite3", "sqlalchemy", "prisma"]
        matched_db_libs = [lib for lib in db_libs if lib in dependencies]
        db_score += len(matched_db_libs) * 20
        db_score = min(100, db_score)

        # 4. Authentication Score
        auth_score = 20
        if features.get("authentication"):
            auth_score += 50
        auth_keywords = ["auth", "login", "jwt", "passport", "bcrypt", "session", "oauth", "password"]
        if any(any(k in f.lower() for k in auth_keywords) for f in files_list) or any(any(k in dep for k in auth_keywords) for dep in dependencies):
            auth_score += 30
        auth_score = min(100, auth_score)

        # 5. Deployment Score
        deploy_score = 10
        if features.get("docker"):
            deploy_score += 50
        
        has_cicd = any(".github/workflows" in f or ".gitlab-ci.yml" in f for f in files_list)
        if has_cicd:
            deploy_score += 20
        if "docker-compose.yml" in config_files or "docker-compose.yaml" in config_files or "Dockerfile" in config_files:
            deploy_score += 20
        deploy_score = min(100, deploy_score)

        # 6. Testing Score
        test_score = 10
        if features.get("testing"):
            test_score += 50
        test_keywords = ["test", "spec", "jest", "mocha", "chai", "pytest", "unittest"]
        has_test_files = any(any(k in f.lower() for k in test_keywords) for f in files_list)
        has_test_deps = any(any(k in dep for k in test_keywords) for dep in dependencies)
        if has_test_files or has_test_deps:
            test_score += 40
        test_score = min(100, test_score)

        # 7. Documentation Score
        doc_score = 20
        if any(f.endswith("README.md") for f in files_list):
            doc_score += 40
        doc_files = ["contributing.md", "architecture.md", ".env.example", "setup.md", "api.md"]
        matched_docs = [d for d in doc_files if any(f.lower().endswith(d) for f in files_list)]
        doc_score += len(matched_docs) * 20
        doc_score = min(100, doc_score)

        # 8. Architecture Score
        arch_score = 40
        folder_patterns = ["components", "routes", "services", "controllers", "models", "utils", "config", "tests"]
        matched_patterns = [p for p in folder_patterns if any(p + "/" in f for f in files_list)]
        arch_score += len(matched_patterns) * 8
        if len(files_list) > 15:
            arch_score += 10
        arch_score = min(100, arch_score)

        # 9. Business Logic Score
        bl_score = 30
        logic_patterns = ["services", "logic", "utils", "helpers"]
        if any(any(p + "/" in f for p in logic_patterns) for f in files_list) or any("utils" in f or "helper" in f for f in files_list):
            bl_score += 40
        source_files = [f for f in files_list if f.split(".")[-1] in ["py", "js", "jsx", "ts", "tsx"]]
        if len(source_files) > 5:
            bl_score += 30
        bl_score = min(100, bl_score)

        # Calculate Overall Authenticity Score (weighted average)
        overall_score = int(
            0.15 * arch_score +
            0.15 * be_score +
            0.10 * fe_score +
            0.10 * auth_score +
            0.10 * db_score +
            0.15 * bl_score +
            0.10 * deploy_score +
            0.10 * test_score +
            0.05 * doc_score
        )

        # Determine Classification
        if overall_score >= 85:
            classification = "Production Ready"
        elif overall_score >= 70:
            classification = "Mostly Complete"
        elif overall_score >= 50:
            classification = "Frontend Heavy"
        else:
            classification = "Superficial"

        # Determine Missing Components
        missing = []
        if db_score < 50:
            missing.append("Database persistence or caching adapter layers")
        if auth_score < 50:
            missing.append("User identity management and session validation (JWT/OAuth)")
        if deploy_score < 50:
            missing.append("Containerization (Dockerfile) or deployment workflows")
        if test_score < 50:
            missing.append("Unit testing modules or automated test specs")
        if doc_score < 50:
            missing.append("Detailed developer documentation or environment config examples")
        if be_score < 50:
            missing.append("Modular API endpoint router / controllers")
        if fe_score < 50:
            missing.append("Structured frontend modules / styling libraries")

        if not missing:
            missing.append("No major missing components identified.")

        # Gather Evidence files
        evidence = []
        critical_configs = ["package.json", "requirements.txt", "docker-compose.yml", "Dockerfile", ".env.example"]
        for f in critical_configs:
            if f in config_files:
                evidence.append(f"Identified configuration manifest: {f}")
        
        test_files = [f for f in files_list if "test" in f.lower() or "spec" in f.lower()][:3]
        for tf in test_files:
            evidence.append(f"Found verification test script: {tf}")
            
        if len(api_routes) > 0:
            evidence.append(f"Detected API Route bindings (e.g. {api_routes[0]})")

        if not evidence:
            evidence.append("Rule engine could not locate distinct codebase markers.")

        return {
            "score": overall_score,
            "classification": classification,
            "category_scores": {
                "architecture": arch_score,
                "backend": be_score,
                "frontend": fe_score,
                "authentication": auth_score,
                "database": db_score,
                "businessLogic": bl_score,
                "deployment": deploy_score,
                "testing": test_score,
                "documentation": doc_score
            },
            "missing_indicators": missing,
            "real_indicators": evidence,
            "superficial_indicators": [
                "Boilerplate files found in root structure"
            ] if len(files_list) < 10 else [
                "Common package/project structure matches boilerplate baselines"
            ]
        }
