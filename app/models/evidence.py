"""
Pydantic data models for the Evidence Object schema.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    """Metadata about the submitted project."""
    title: str = Field(..., description="The stated title of the project.")
    description: Optional[str] = Field(None, description="The stated description of the project.")
    outcomes: List[str] = Field(default_factory=list, description="Expected learning/project outcomes.")


class ProjectStatistics(BaseModel):
    """Static statistics of the codebase."""
    total_files: int = Field(default=0, description="Total count of files discovered.")
    source_files: int = Field(default=0, description="Total count of analyzed source files.")
    directories: int = Field(default=0, description="Total count of directories discovered.")
    lines_of_code: int = Field(default=0, description="Estimated total lines of source code.")


class LanguageEvidence(BaseModel):
    """Evidence of a programming language detected in the codebase."""
    name: str = Field(..., description="The programming language name (e.g. Python).")
    confidence: float = Field(..., description="Language confidence score between 0.0 and 1.0.")


class FrameworkEvidence(BaseModel):
    """Evidence of a software framework detected in the codebase."""
    name: str = Field(..., description="The software framework name (e.g. FastAPI).")
    evidence: List[str] = Field(default_factory=list, description="Files indicating framework presence.")


class DependencyEvidence(BaseModel):
    """Evidence of a package or library dependency."""
    name: str = Field(..., description="The package or dependency name.")
    version: Optional[str] = Field(None, description="The detected version string.")


class FileEvidence(BaseModel):
    """Details of a single source file in the codebase."""
    path: str = Field(..., description="The relative path of the file.")
    language: str = Field(..., description="The programming language of the file.")
    size: int = Field(..., description="File size in bytes.")


class ClassEvidence(BaseModel):
    """Details of a class discovered in the codebase."""
    name: str = Field(..., description="The class name.")
    file: str = Field(..., description="The relative file path containing the class.")


class FunctionEvidence(BaseModel):
    """Details of a function discovered in the codebase."""
    name: str = Field(..., description="The function name.")
    file: str = Field(..., description="The relative file path containing the function.")


class RouteEvidence(BaseModel):
    """Details of an HTTP route or API endpoint discovered in the codebase."""
    method: str = Field(..., description="The HTTP verb (GET, POST, etc.).")
    path: str = Field(..., description="The endpoint path pattern.")
    file: str = Field(..., description="The relative file path defining the endpoint.")


class DatabaseEvidence(BaseModel):
    """Evidence of a database technology used in the codebase."""
    type: str = Field(..., description="The database type (e.g. SQLite, PostgreSQL).")
    evidence: List[str] = Field(default_factory=list, description="Files indicating database usage.")


class DeploymentEvidence(BaseModel):
    """Evidence of deployment configuration or environment."""
    type: str = Field(..., description="The deployment technology name (e.g. Docker).")
    files: List[str] = Field(default_factory=list, description="Discovered deployment configuration files.")


class TestingEvidence(BaseModel):
    """Evidence of testing framework usage."""
    framework: str = Field(..., description="The testing framework name (e.g. pytest).")
    files: int = Field(default=0, description="The number of test files discovered.")


class DocumentationEvidence(BaseModel):
    """Evidence of project documentation files."""
    type: str = Field(..., description="The documentation type (README, LICENSE, etc.).")
    file: str = Field(..., description="The relative path of the documentation file.")


class ConfigurationEvidence(BaseModel):
    """Evidence of project configuration files."""
    file: str = Field(..., description="The relative path of the configuration file.")


class EvidenceMetadata(BaseModel):
    """Processing metadata for the evidence extraction process."""
    parser_version: str = Field(..., description="Version of the static parser engine.")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds.")
    generated_at: str = Field(..., description="ISO 8601 timestamp of generation.")


class Evidence(BaseModel):
    """Canonical Evidence Object contract between static analysis and AI layer."""
    schema_version: str = Field("1.0", description="Version of the evidence schema.")
    project: ProjectInfo = Field(..., description="Project basic metadata.")
    statistics: ProjectStatistics = Field(default_factory=ProjectStatistics, description="Project statistics.")
    languages: List[LanguageEvidence] = Field(default_factory=list, description="List of detected programming languages.")
    frameworks: List[FrameworkEvidence] = Field(default_factory=list, description="List of detected software frameworks.")
    dependencies: List[DependencyEvidence] = Field(default_factory=list, description="List of detected package dependencies.")
    files: List[FileEvidence] = Field(default_factory=list, description="Catalog of discovered source code files.")
    directories: List[str] = Field(default_factory=list, description="List of relative directory paths.")
    classes: List[ClassEvidence] = Field(default_factory=list, description="List of classes detected in the codebase.")
    functions: List[FunctionEvidence] = Field(default_factory=list, description="List of functions detected in the codebase.")
    routes: List[RouteEvidence] = Field(default_factory=list, description="List of HTTP API routes detected.")
    databases: List[DatabaseEvidence] = Field(default_factory=list, description="List of database technologies detected.")
    deployment: List[DeploymentEvidence] = Field(default_factory=list, description="List of deployment platforms or files.")
    testing: List[TestingEvidence] = Field(default_factory=list, description="List of testing frameworks and files.")
    documentation: List[DocumentationEvidence] = Field(default_factory=list, description="List of documentation files.")
    configuration: List[ConfigurationEvidence] = Field(default_factory=list, description="List of configuration files.")
    metadata: EvidenceMetadata = Field(..., description="Analysis processing metadata.")
