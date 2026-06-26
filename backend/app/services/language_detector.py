from typing import List, Dict, Any

EXTENSION_MAP = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".groovy": "Groovy",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".hh": "C++",
    ".hxx": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".swift": "Swift",
    ".php": "PHP",
    ".rb": "Ruby",
    ".dart": "Dart",
    ".lua": "Lua",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "CSS",
    ".sass": "CSS",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".txt": "Text",
}

def detect_languages(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculates LOC per language and percentage.
    """
    loc_by_lang = {}
    total_loc = 0
    
    for f in files:
        ext = f.get("extension", "").lower()
        lang = EXTENSION_MAP.get(ext, "Unknown")
        
        content = f.get("content", "")
        lines = content.split("\n")
        loc = len([line for line in lines if line.strip()])
        
        if loc == 0:
            loc = 1
            
        loc_by_lang[lang] = loc_by_lang.get(lang, 0) + loc
        total_loc += loc
        
    if total_loc == 0:
        total_loc = 1
        
    language_analysis = []
    for lang, loc in loc_by_lang.items():
        percentage = (loc / total_loc) * 100
        language_analysis.append({
            "language": lang,
            "loc": loc,
            "percentage": round(percentage, 2)
        })
        
    language_analysis.sort(key=lambda x: x["percentage"], reverse=True)
    return language_analysis
