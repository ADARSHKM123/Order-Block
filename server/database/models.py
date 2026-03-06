"""SQLAlchemy database models."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    input_path = Column(String, nullable=False)
    output_path = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    settings_json = Column(Text, default="{}")
    summary_json = Column(Text, default="{}")
    results_json = Column(Text, default="[]")
    clusters_json = Column(Text, default="{}")
    cluster_assignments_json = Column(Text, default="[]")
    best_picks_json = Column(Text, default="[]")
    image_count = Column(Integer, default=0)
