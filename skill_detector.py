from typing import Dict, List, Any

extension_map = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".html": "HTML",
    ".css": "CSS",
    ".java": "Java",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".php": "PHP",
    ".rb": "Ruby",
    ".sql": "SQL",
    ".jsx": "React",
    ".tsx": "TypeScript/React",
    ".vue": "Vue.js",
    ".rs": "Rust",
    ".kt": "Kotlin",
    ".swift": "Swift"
}

framework_signals = {
    "React": ["import React", "useState", "useEffect", "ReactDOM"],
    "Flask": ["from flask", "import Flask", "@app.route"],
    "FastAPI": ["from fastapi", "import FastAPI", "APIRouter"],
    "Django": ["from django", "import django", "urlpatterns"],
    "Express": ["require('express')", "import express", "app.get("],
    "Next.js": ["from 'next'", "import next", "getStaticProps"],
    "Vue.js": ["<template>", "import Vue", "createApp"],
    "Spring": ["@SpringBootApplication", "@RestController", "import org.springframework"],
    "Node.js": ["require(", "module.exports", "process.env"],
    "TensorFlow": ["import tensorflow", "import tf", "tf.keras"],
    "PyTorch": ["import torch", "torch.nn"],
    "Pandas": ["import pandas", "import pd"],
    "NumPy": ["import numpy", "import np"]
}

def detect_skills(extensions: Dict[str, int], source_code: str) -> Dict[str, Any]:
    """
    Detect languages from extensions and frameworks from source code signals.
    Calculates language percentages.
    """
    lang_counts = {}
    total_matched_files = 0
    
    # 1. Count files per language mapped
    for ext, count in extensions.items():
        lang = extension_map.get(ext.lower())
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + count
            total_matched_files += count
            
    # 2. Calculate percentages
    languages_pct = {}
    if total_matched_files > 0:
        for lang, count in lang_counts.items():
            languages_pct[lang] = round((count / total_matched_files) * 100.0, 1)
            
    # 3. Determine primary language
    primary_language = None
    if lang_counts:
        primary_language = max(lang_counts, key=lang_counts.get)
        
    # 4. Detect frameworks
    detected_frameworks = []
    for framework, signals in framework_signals.items():
        for sig in signals:
            if sig in source_code:
                detected_frameworks.append(framework)
                break  # Stop checking this framework if one signal matches
                
    # 5. Compile all skills (languages + frameworks)
    all_skills = list(languages_pct.keys()) + detected_frameworks
    
    return {
        "languages": languages_pct,
        "frameworks": detected_frameworks,
        "primary_language": primary_language or "Unknown",
        "all_skills": all_skills
    }
