"""Seed demo activities.

Both seeders accept an optional center (lat, lon) so the organizer can start
the activity at the current location. Idempotent for hide-and-seek.
"""
from __future__ import annotations

import json
from sqlmodel import Session, select

from .db import engine
from .models import Activity, Zone, Track, TrackPoint, Detection
from .services import detect

LAT0, LON0 = 30.2500, 120.1300  # fallback demo center


def _rect(cx, cy, w, h):
    """Rectangle polygon [[lon,lat],...] centered at (cx=lon, cy=lat)."""
    return [[cx - w, cy - h], [cx + w, cy - h], [cx + w, cy + h], [cx - w, cy + h]]


def seed_if_empty(center_lat: float = LAT0, center_lon: float = LON0) -> int | None:
    cy, cx = center_lat, center_lon
    with Session(engine) as s:
        if s.exec(select(Activity)).first():
            return None

        a = Activity(name="Hide and Seek 演示场", scenario="hide_and_seek",
                     center_lat=cy, center_lon=cx, zoom=15.5)
        s.add(a)
        s.commit()
        s.refresh(a)

        s.add_all([
            Zone(activity_id=a.id, name="活动区", kind="activity", role_owner="organizer",
                 polygon_json=json.dumps(_rect(cx, cy, 0.0090, 0.0060))),
            Zone(activity_id=a.id, name="搜索区", kind="search", role_owner="search",
                 polygon_json=json.dumps(_rect(cx - 0.0040, cy, 0.0040, 0.0050))),
            Zone(activity_id=a.id, name="防护/隐藏区", kind="protection", role_owner="protection",
                 polygon_json=json.dumps(_rect(cx + 0.0045, cy, 0.0035, 0.0045))),
            Zone(activity_id=a.id, name="禁入区", kind="no_go", role_owner="organizer",
                 polygon_json=json.dumps(_rect(cx, cy + 0.0010, 0.0010, 0.0018))),
            Zone(activity_id=a.id, name="安全区", kind="safe", role_owner="organizer",
                 polygon_json=json.dumps(_rect(cx - 0.0075, cy - 0.0045, 0.0012, 0.0010))),
        ])
        s.commit()

        tr = Track(activity_id=a.id, name="搜索方扫描航迹", team="search", source="gpx")
        s.add(tr)
        s.commit()
        s.refresh(tr)
        seq = 0
        rows = 6
        for r in range(rows):
            lat = cy - 0.0045 + r * (0.0090 / (rows - 1))
            lon_a, lon_b = cx - 0.0078, cx - 0.0002
            xs = [lon_a, lon_b] if r % 2 == 0 else [lon_b, lon_a]
            for lon in xs:
                s.add(TrackPoint(track_id=tr.id, seq=seq, lat=round(lat, 6), lon=round(lon, 6)))
                seq += 1
        s.commit()

        pts = s.exec(select(TrackPoint).where(TrackPoint.track_id == tr.id)
                     .order_by(TrackPoint.seq)).all()
        for d in detect.simulate_along_track([{"lat": p.lat, "lon": p.lon} for p in pts],
                                              count=7, seed=7):
            s.add(Detection(activity_id=a.id, label=d["label"], confidence=d["confidence"],
                            lat=d["lat"], lon=d["lon"], simulated=True))
        s.commit()
        return a.id


def seed_sar(center_lat: float = LAT0, center_lon: float = LON0) -> int:
    """Fresh SAR activity (organizer + search): activity zone, search zone,
    two safe zones (start/evacuation), one no-go. Targets placed as an action."""
    cy, cx = center_lat, center_lon
    with Session(engine) as s:
        a = Activity(name="野外搜救 演示场", scenario="sar",
                     center_lat=cy, center_lon=cx, zoom=15.0)
        s.add(a)
        s.commit()
        s.refresh(a)
        s.add_all([
            Zone(activity_id=a.id, name="活动区", kind="activity", role_owner="organizer",
                 polygon_json=json.dumps(_rect(cx, cy, 0.0100, 0.0070))),
            Zone(activity_id=a.id, name="重点搜索区", kind="search", role_owner="search",
                 polygon_json=json.dumps(_rect(cx + 0.0010, cy, 0.0055, 0.0045))),
            Zone(activity_id=a.id, name="出发点(安全区1)", kind="safe", role_owner="organizer",
                 polygon_json=json.dumps(_rect(cx - 0.0082, cy - 0.0055, 0.0012, 0.0010))),
            Zone(activity_id=a.id, name="撤离点(安全区2)", kind="safe", role_owner="organizer",
                 polygon_json=json.dumps(_rect(cx + 0.0082, cy + 0.0055, 0.0012, 0.0010))),
            Zone(activity_id=a.id, name="禁入区(危险)", kind="no_go", role_owner="organizer",
                 polygon_json=json.dumps(_rect(cx + 0.0010, cy - 0.0030, 0.0010, 0.0012))),
        ])
        s.commit()
        return a.id
