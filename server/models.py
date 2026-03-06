"""Pydantic request/response models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Enums ---

class SessionStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    error = "error"
    cancelled = "cancelled"


class QualityCategory(str, Enum):
    good = "good"
    blurry = "blurry"
    overexposed = "overexposed"
    underexposed = "underexposed"


# --- Request Models ---

class CreateSessionRequest(BaseModel):
    name: Optional[str] = None
    input_path: str
    output_path: str


class ProcessingSettings(BaseModel):
    blur_threshold: float = 100.0
    overexposure_threshold: float = 220.0
    underexposure_threshold: float = 40.0
    workers: int = 4
    move: bool = False
    cluster: bool = True
    fast: bool = False
    similarity_threshold: float = 0.25
    min_cluster_size: int = 2
    batch_size: int = 32
    hash_threshold: int = 15


class StartProcessingRequest(BaseModel):
    settings: ProcessingSettings = Field(default_factory=ProcessingSettings)


class OverrideRequest(BaseModel):
    overrides: Dict[str, str]  # cluster_id -> filename


class BrowseRequest(BaseModel):
    path: Optional[str] = None


# --- Response Models ---

class QualityResult(BaseModel):
    filename: str
    original_path: str
    category: str
    sharpness_laplacian: float
    sharpness_tenengrad: float
    brightness_mean: float
    brightness_std: float
    noise_estimate: float
    quality_score: float
    is_blurry: bool
    is_overexposed: bool
    is_underexposed: bool


class ClusterAssignment(BaseModel):
    filename: str
    original_path: str
    cluster_id: Any  # int or "unique"
    cluster_folder: str


class BestPick(BaseModel):
    filename: str
    original_path: str
    source: str
    cluster_id: int
    quality_score: float
    selection_reason: str


class SessionSummary(BaseModel):
    total: int = 0
    good: int = 0
    blurry: int = 0
    overexposed: int = 0
    underexposed: int = 0
    errors: int = 0
    num_clusters: Optional[int] = None
    num_unique: Optional[int] = None
    num_best_picks: Optional[int] = None


class SessionResponse(BaseModel):
    id: str
    name: str
    input_path: str
    output_path: str
    status: SessionStatus
    created_at: str
    updated_at: str
    settings: Optional[ProcessingSettings] = None
    summary: Optional[SessionSummary] = None
    image_count: int = 0


class ResultsResponse(BaseModel):
    quality_results: List[QualityResult]
    cluster_assignments: List[ClusterAssignment]
    best_picks: List[BestPick]
    summary: SessionSummary
    clusters: Dict[str, List[QualityResult]]


class FolderEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    image_count: Optional[int] = None


class BrowseResponse(BaseModel):
    current_path: str
    parent_path: Optional[str]
    entries: List[FolderEntry]
    drives: Optional[List[str]] = None
