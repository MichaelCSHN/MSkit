"""Seed a demo Hide-and-Seek activity so the app has content on first run.

Idempotent: does nothing if any activity already exists.
"""
from __future__ import annotations

import json
from sqlmodel import Session, select

from .db import engine
from .models import Activity, Zone, Track, TrackPoint, Detection
from .services import detect

LAT0, LON0 = 30.2500, 120.1300  # demo center


def _rect(cx, cy, w, h):
    """Rectangle polygon [[lon,lat],...] centered at (cx=lon, cy=lat)."""
    return [[cx - w, cy - h], [cx + w, cy - h], [cx + w, cy + h], [cx - w, cy + h]]


def seed_if_empty() -> int | None:
    with Session(engine) as s:
        if s.exec(select(Activity)).first():
            return None

        a = Activity(name="Hide and Seek 演示场", scenario="hide_and_seek",
                     center_lat=LAT0, center_lon=LON0, zoom=15.5)
        s.add(a)
        s.commit()
        s.refresh(a)

        zones = [
            Zone(activity_id=a.id, name="活动区", kind="activity", role_owner="organizer",
                 polygon_json=json.dumps(_rect(LON0, LAT0, 0.0090, 0.0060))),
            Zone(activity_id=a.id, name="搜索区", kind="search", role_owner="search",
                 polygon_json=json.dumps(_rect(LON0 - 0.0040, LAT0, 0.0040, 0.0050))),
            Zone(activity_id=a.id, name="防护/隐藏区", kind="protection", role_owner="protection",
                 polygon_json=json.dumps(_rect(LON0 + 0.0045, LAT0, 0.0035, 0.0045))),
            Zone(activity_id=a.id, name="禁入区", kind="no_go", role_owner="organizer",
                 polygon_json=json.dumps(_rect(LON0, LAT0 + 0.0010, 0.0010, 0.0018))),
            Zone(activity_id=a.id, name="安全区", kind="safe", role_owner="organizer",
                 polygon_json=json.dumps(_rect(LON0 - 0.0075, LAT0 - 0.0045, 0.0012, 0.0010))),
        ]
        s.add_all(zones)
        s.commit()

        # search-side sweep track (zigzag) inside the search zone
        tr = Track(activity_id=a.id, name="搜索方扫描航迹", team="search", source="gpx")
        s.add(tr)
        s.commit()
        s.refresh(tr)
        seq = 0
        rows = 6
        for r in range(rows):
            lat = LAT0 - 0.0045 + r * (0.0090 / (rows - 1))
            lon_a, lon_b = LON0 - 0.0078, LON0 - 0.0002
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
