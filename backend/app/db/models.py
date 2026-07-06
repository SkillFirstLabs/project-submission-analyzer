import time
from sqlalchemy import Column, String, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "student" or "mentor"
    name = Column(String, nullable=False)
    created_at = Column(Float, default=time.time)

    submissions = relationship("Submission", back_populates="student")
    mentored_sessions = relationship("VivaSession", back_populates="mentor")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    project_title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    outcomes = Column(String, nullable=False)
    zip_path = Column(String, nullable=False)
    created_at = Column(Float, default=time.time)

    student = relationship("User", back_populates="submissions")
    evaluation_report = relationship("EvaluationReport", back_populates="submission", uselist=False)
    viva_session = relationship("VivaSession", back_populates="submission", uselist=False)

class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id = Column(String, primary_key=True, index=True)
    submission_id = Column(String, ForeignKey("submissions.id"), unique=True, nullable=False)
    suggested_skills = Column(JSON, nullable=False)
    evaluation_report = Column(JSON, nullable=False)
    created_at = Column(Float, default=time.time)

    submission = relationship("Submission", back_populates="evaluation_report")

class VivaSession(Base):
    __tablename__ = "viva_sessions"

    id = Column(String, primary_key=True, index=True)
    submission_id = Column(String, ForeignKey("submissions.id"), unique=True, nullable=False)
    mentor_id = Column(String, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed
    id_check = Column(String, default="pending")
    integrity_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    started_at = Column(Float, nullable=True)
    ended_at = Column(Float, nullable=True)
    
    events = relationship("VivaEvent", back_populates="session")
    flags = Column(JSON, default=list)
    last_event_at = Column(Float, nullable=True)
    proctoring_report = Column(JSON, nullable=True)
    viva_grading = Column(JSON, nullable=True)
    
    submission = relationship("Submission", back_populates="viva_session")
    mentor = relationship("User", back_populates="mentored_sessions")

class VivaEvent(Base):
    __tablename__ = "viva_events"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("viva_sessions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    duration_ms = Column(Float, default=0.0)
    confidence = Column(Float, default=1.0)
    severity = Column(String, nullable=True)

    session = relationship("VivaSession", back_populates="events")
