import os


FRAMEWORK_PATTERNS = {
    "FastAPI": [
        "from fastapi",
        "FastAPI("
    ],

    "Flask": [
        "from flask",
        "Flask("
    ],

    "Django": [
        "manage.py",
        "django",
        "INSTALLED_APPS"
    ],

    "React": [
        "react",
        "react-dom",
        "useState",
        "useEffect",
        "package.json"
    ],

    "Angular": [
        "@angular/core",
        "angular.json"
    ],

    "Vue": [
        "vue",
        "createApp("
    ],

    "Spring Boot": [
        "@SpringBootApplication",
        "spring-boot-starter"
    ],

    "Express.js": [
        "express(",
        "require('express')",
        'require("express")'
    ]
}


def detect_frameworks(project_path: str):
    detected = set()

    for root, _, files in os.walk(project_path):

        for file in files:

            file_path = os.path.join(root, file)

            try:
                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as f:

                    content = f.read().lower()

                    for framework, patterns in FRAMEWORK_PATTERNS.items():

                        for pattern in patterns:

                            if pattern.lower() in content:
                                detected.add(framework)

            except Exception:
                pass

    return sorted(list(detected))