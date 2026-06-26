import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
    
    # FAISS config
    FAISS_INDEX_PATH: str = "faiss_index"
    
    # Upload limits (50MB)
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS: set = {
        # Python
        ".py", ".pyi",
        # JS/TS
        ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx",
        # Java
        ".java", ".kt", ".kts", ".scala", ".groovy",
        # C/C++
        ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx",
        # Go, Rust, Ruby, etc.
        ".go", ".rs", ".rb", ".php", ".cs", ".swift", ".dart", ".lua", ".sh",
        # Web
        ".html", ".htm", ".css", ".scss", ".sass", ".vue", ".svelte",
        # Config
        ".json", ".yaml", ".yml", ".toml", ".xml",
        # Docs
        ".md", ".mdx", ".txt",
    }
    
    ALWAYS_INCLUDE_NAMES: set = {
        "dockerfile", "docker-compose.yml", "docker-compose.yaml", "makefile",
        "readme", "requirements.txt", "package.json", "pom.xml", "build.gradle",
        "go.mod", "cargo.toml", ".gitignore", "pubspec.yaml",
    }
    
    SKIP_DIRS: set = {
        "node_modules", ".git", "dist", "build", "__pycache__",
        "venv", ".env", "env", "target", "vendor", ".next",
    }

settings = Settings()
