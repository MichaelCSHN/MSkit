"""Data model for the MVP.

Roles are the neutral tri-party model (see docs/MSkit_v1.3.2_Tri_Party_Functions.md):
  - organizer  (组织方)  : global view, config, PNT/timeline, planning, report
  - search     (搜索方)  : detection / change / evidence
  - protection (防护方)  : coverage planning, zones, patrol
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


ROLES = ("organizer", "search", "protection")
# Zone kinds and which role owns them.
ZONE_KINDS = ("activity", "search", "protection", "no_go", "safe", "staging")


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    scenario: str = "hide_and_seek"  # hide_and_seek | sar | milsim | security | ...
    center_lat: float = 0.0
    center_lon: float = 0.0
    zoom: float = 15.0
    created_at: datetime = Field(default_factory=_utcnow)


class Zone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(foreign_key="activity.id", index=True)
    name: str
    kind: str = "activity"          # see ZONE_KINDS
    role_owner: str = "organizer"   # organizer | search | protection
    # Polygon as JSON string: [[lon,lat], ...] (GeoJSON ring order, lon first)
    polygon_json: str = "[]"


class Track(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(foreign_key="activity.id", index=True)
    name: str
    team: str = "search"            # organizer | search | protection
    source: str = "manual"          # gpx | csv | srt | manual
    created_at: datetime = Field(default_factory=_utcnow)


class TrackPoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key="track.id", index=True)
    seq: int = 0
    lat: float = 0.0
    lon: float = 0.0
    ele: Optional[float] = None
    ts: Optional[datetime] = None


class Detection(SQLModel, table=True):
    """Search-side object/change detection result mapped to the map."""
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(foreign_key="activity.id", index=True)
    kind: str = "object"            # object detection | change detection
    label: str = "person"           # person | vehicle | animal | facility | heat | change
    confidence: float = 0.0
    lat: float = 0.0
    lon: float = 0.0
    ts: datetime = Field(default_factory=_utcnow)
    media_ref: Optional[str] = None
    status: str = "candidate"       # candidate | confirmed | rejected
    simulated: bool = True          # MVP honesty: real inference vs pre-seeded/simulated
    note: Optional[str] = None


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(foreign_key="activity.id", index=True)
    type: str = "detection"         # detection | change | breach | found | note
    role: str = "search"
    lat: Optional[float] = None
    lon: Optional[float] = None
    ts: datetime = Field(default_factory=_utcnow)
    detail: Optional[str] = None
