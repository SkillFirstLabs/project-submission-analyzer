from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")
    port: int = Field(default=8000, validation_alias="PORT")
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    
    # Thresholds
    gaze_off_screen_threshold_sec: float = Field(default=3.0, validation_alias="GAZE_OFF_SCREEN_THRESHOLD_SEC")
    face_not_detected_threshold_sec: float = Field(default=5.0, validation_alias="FACE_NOT_DETECTED_THRESHOLD_SEC")
    connection_lost_timeout_sec: float = Field(default=15.0, validation_alias="CONNECTION_LOST_TIMEOUT_SEC")
    user_inactive_threshold_sec: float = Field(default=15.0, validation_alias="USER_INACTIVE_THRESHOLD_SEC")
    
    # Penalties
    gaze_off_screen_penalty: float = Field(default=0.05, validation_alias="GAZE_OFF_SCREEN_PENALTY")
    multiple_faces_penalty: float = Field(default=0.2, validation_alias="MULTIPLE_FACES_PENALTY")
    face_not_detected_penalty: float = Field(default=0.1, validation_alias="FACE_NOT_DETECTED_PENALTY")
    tab_switched_penalty: float = Field(default=0.1, validation_alias="TAB_SWITCHED_PENALTY")
    fullscreen_exited_penalty: float = Field(default=0.15, validation_alias="FULLSCREEN_EXITED_PENALTY")
    paste_attempted_penalty: float = Field(default=0.1, validation_alias="PASTE_ATTEMPTED_PENALTY")
    screenshot_detected_penalty: float = Field(default=0.2, validation_alias="SCREENSHOT_DETECTED_PENALTY")
    connection_lost_penalty: float = Field(default=0.3, validation_alias="CONNECTION_LOST_PENALTY")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
