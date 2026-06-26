from app.models.project_context import ProjectContext


class DeepRankingService:

    MAX_FILES = 15

    def process(self, context: ProjectContext) -> ProjectContext:

        scored_files = []

        for file in context.loaded_files:

            if not file.loaded:
                continue

            score = 0
            reasons = []

            content = file.content.lower()

            # --------------------------
            # Framework Detection
            # --------------------------
            if "fastapi" in content:
                score += 40
                reasons.append("Uses FastAPI framework")

            if "flask" in content:
                score += 35
                reasons.append("Uses Flask framework")

            if "spring" in content or "@restcontroller" in content:
                score += 40
                reasons.append("Spring Boot / REST API detected")

            # --------------------------
            # API Layer Detection
            # --------------------------
            if "@app." in content or "apirouter" in content:
                score += 30
                reasons.append("API route definitions found")

            if "router.post" in content or "router.get" in content:
                score += 25
                reasons.append("REST endpoints defined")

            # --------------------------
            # Authentication Detection
            # --------------------------
            if "jwt" in content:
                score += 30
                reasons.append("JWT authentication detected")

            if "oauth" in content:
                score += 25
                reasons.append("OAuth integration")

            if "bcrypt" in content:
                score += 20
                reasons.append("Password hashing detected")

            # --------------------------
            # Database Detection
            # --------------------------
            if "sqlalchemy" in content:
                score += 25
                reasons.append("SQLAlchemy ORM used")

            if "mongodb" in content:
                score += 20
                reasons.append("MongoDB integration")

            if "psycopg" in content or "postgres" in content:
                score += 20
                reasons.append("PostgreSQL usage detected")

            # --------------------------
            # Architecture Quality
            # --------------------------
            if "class " in content:
                score += 10
                reasons.append("OOP structure present")

            if "def " in content:
                score += 5

            if "service" in file.path.lower():
                score += 10
                reasons.append("Service layer architecture")

            if "controller" in file.path.lower():
                score += 10
                reasons.append("Controller layer detected")

            # --------------------------
            # Update File
            # --------------------------
            file.deep_score = score
            file.deep_reasons = reasons

            scored_files.append(file)

        # Sort by deep score
        scored_files.sort(key=lambda x: x.deep_score, reverse=True)

        # Select top files
        context.deeply_ranked_files = scored_files[: self.MAX_FILES]

        # Metadata
        context.metadata["deep_ranked_files_count"] = len(context.deeply_ranked_files)

        return context