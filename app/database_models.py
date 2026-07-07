from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime, timezone
from app.database import Base

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    # -----------------------------------------------
    # PRIMARY KEY
    # -----------------------------------------------
    session_id = Column(
        String,
        primary_key=True,
        index=True
    )

    # -----------------------------------------------
    # SESSION DATA
    # -----------------------------------------------
    project_analysis = Column(
        Text,
        nullable=True
    )
    viva_evaluation = Column(
        Text,
        nullable=True
    )
    proctoring_report = Column(
        Text,
        nullable=True
    )
    final_assessment = Column(
        Text,
        nullable=True
    )

    # -----------------------------------------------
    # TIMESTAMPS
    # -----------------------------------------------
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
