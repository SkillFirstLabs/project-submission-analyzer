import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Path settings
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    SKILL_CATALOG_PATH: Path = DATA_DIR / "skill_catalog.json"
    
    # Secure extraction limits
    MAX_UNCOMPRESSED_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB
    MAX_COMPRESSION_RATIO: float = 100.0
    MAX_FILE_READ_SIZE_BYTES: int = 500 * 1024  # 500 KB per source file to prevent huge reads

settings = Settings()
