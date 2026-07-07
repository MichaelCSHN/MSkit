"""HTTP API for the MVP tri-party platform."""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from .db import get_session
from .models import Activity, Zone, Track, TrackPoint, Detection, Event, ROLES
from . import geo
from .services import logparse, detect, report

router = APIRouter()

# ---- role-based visibility (MVP simplified) -------------------------------
ZONES_BY_ROLE = {
    "organizer": None,  # all
    "search": {"activity", "search", "no_go", "safe", "staging"},
    "protection": {"activity", "protection", "no_go", "safe", "staging"},
}
TRACK_TEAMS_BY_ROLE = {
    "organizer": None,
    "search": {"search", "organizer"},
    "protection": {"protection", "organizer"},
}


def _check_role(role: str) -> str:
    if role not in ROLES:
        raise HTTPException(400, f"role must be one of {ROLES}")
    return role


def _get_activity(session: Session, activity_id: int) -> Activity:
    a = session.get(Activity, activity_id)
    if not a:
        raise HTTPException(404, "activity not found")
    return a


# ---- request bodies -------------------------------------------------------
class ActivityIn(BaseModel):
    name: str
    scenario: str = "hide_and_seek"
    center_lat: float = 0.0
    center_lon: float = 0.0
    zoom: float = 15.0


class ZoneIn(BaseModel):
    name: str
    kind: str = "activity"
    role_owner: str = "organizer"
    polygon: list[list[float]]  # [[lon,lat], ...]


class DetectionIn(BaseModel):
    label: str = "person"
    kind: str = "object"
    confidence: float = 0.9
    lat: float
    lon: float
    simulated: bool = True
    note: Optional[str] = None


class SimulateIn(BaseModel):
    track_id: int
    count: int = 6
    classes: Optional[list[str]] = None


class ChangeIn(BaseModel):
    zone_kind: str = "activity"   # sample change points within this zone kind
    count: int = 5
    seed: int = 3


class ReviewIn(BaseModel):
    status: str  # confirmed | rejected | candidate
    note: Optional[str] = None


class CoverageIn(BaseModel):
    zone_id: Optional[int] = None
    polygon: Optional[list[list[float]]] = None
    radius_m: float = 120.0
    spacing_m: float = 150.0


class RouteIn(BaseModel):
    start: list[float]  # [lon,lat]
    goal: list[float]   # [lon,lat]
    cell_m: float = 20.0


# ---- health & activities --------------------------------------------------
@router.get("/health")
def health():
    return {"status": "ok", "yolo_available": detect.has_yolo()}


@router.post("/demo/reset")
def demo_reset(session: Session = Depends(get_session)):
    """Wipe all data and re-seed the demo activity (for repeatable pitches)."""
    from sqlmodel import SQLModel
    from .db import engine
    from .seed import seed_if_empty
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    aid = seed_if_empty()
    return {"reset": True, "activity_id": aid}


@router.get("/activities")
def list_activities(session: Session = Depends(get_session)):
    return session.exec(select(Activity)).all()


@router.post("/activities")
def create_activity(body: ActivityIn, session: Session = Depends(get_session)):
    a = Activity(**body.model_dump())
    session.add(a)
    session.commit()
    session.refresh(a)
    return a


@router.get("/activities/{activity_id}")
def get_activity(activity_id: int, session: Session = Depends(get_session)):
    return _get_activity(session, activity_id)


# ---- zones ----------------------------------------------------------------
@router.post("/activities/{activity_id}/zones")
def add_zone(activity_id: int, body: ZoneIn, session: Session = Depends(get_session)):
    _get_activity(session, activity_id)
    z = Zone(activity_id=activity_id, name=body.name, kind=body.kind,
             role_owner=body.role_owner, polygon_json=json.dumps(body.polygon))
    session.add(z)
    session.commit()
    session.refresh(z)
    return z


@router.get("/activities/{activity_id}/zones")
def list_zones(activity_id: int, role: str = "organizer", session: Session = Depends(get_session)):
    _check_role(role)
    zones = session.exec(select(Zone).where(Zone.activity_id == activity_id)).all()
    allowed = ZONES_BY_ROLE[role]
    return [z for z in zones if allowed is None or z.kind in allowed]


# ---- tracks ---------------------------------------------------------------
@router.post("/activities/{activity_id}/tracks")
async def upload_track(activity_id: int, team: str = Form("search"),
                       name: str = Form("track"), file: UploadFile = File(...),
                       session: Session = Depends(get_session)):
    _get_activity(session, activity_id)
    raw = (await file.read()).decode("utf-8", errors="ignore")
    pts = logparse.parse_log(file.filename or "", raw)
    if not pts:
        raise HTTPException(422, "no track points parsed (expect GPX or CSV with lat/lon)")
    src = "gpx" if (file.filename or "").lower().endswith(".gpx") else "csv"
    tr = Track(activity_id=activity_id, name=name, team=team, source=src)
    session.add(tr)
    session.commit()
    session.refresh(tr)
    for p in pts:
        session.add(TrackPoint(track_id=tr.id, seq=p["seq"], lat=p["lat"],
                               lon=p["lon"], ele=p.get("ele"), ts=p.get("ts")))
    session.commit()
    return {"track": tr, "points": len(pts)}


@router.get("/activities/{activity_id}/tracks")
def list_tracks(activity_id: int, role: str = "organizer", session: Session = Depends(get_session)):
    _check_role(role)
    tracks = session.exec(select(Track).where(Track.activity_id == activity_id)).all()
    allowed = TRACK_TEAMS_BY_ROLE[role]
    return [t for t in tracks if allowed is None or t.team in allowed]


# ---- detections -----------------------------------------------------------
@router.post("/activities/{activity_id}/detections/simulate")
def simulate_detections(activity_id: int, body: SimulateIn, session: Session = Depends(get_session)):
    _get_activity(session, activity_id)
    pts = session.exec(
        select(TrackPoint).where(TrackPoint.track_id == body.track_id).order_by(TrackPoint.seq)
    ).all()
    if not pts:
        raise HTTPException(404, "track has no points")
    sims = detect.simulate_along_track(
        [{"lat": p.lat, "lon": p.lon} for p in pts], body.classes, body.count)
    created = []
    for s in sims:
        d = Detection(activity_id=activity_id, label=s["label"], confidence=s["confidence"],
                      lat=s["lat"], lon=s["lon"], simulated=True)
        session.add(d)
        created.append(d)
    session.commit()
    for d in created:
        session.refresh(d)
    return {"created": len(created), "detections": created}


@router.post("/activities/{activity_id}/detections")
def add_detection(activity_id: int, body: DetectionIn, session: Session = Depends(get_session)):
    _get_activity(session, activity_id)
    d = Detection(activity_id=activity_id, **body.model_dump())
    session.add(d)
    session.commit()
    session.refresh(d)
    return d


@router.post("/activities/{activity_id}/detect-image")
async def detect_image_ep(activity_id: int, lat: float = Form(...), lon: float = Form(...),
                          file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Real object detection on an uploaded image (YOLO if installed).

    Detections are tagged at the provided lat/lon (e.g. capture position) and
    flagged simulated=False. Returns [] gracefully if YOLO is unavailable.
    """
    from .db import MEDIA_DIR
    _get_activity(session, activity_id)
    dest = MEDIA_DIR / f"a{activity_id}_{file.filename}"
    dest.write_bytes(await file.read())
    results = detect.detect_image(str(dest))
    created = []
    for r in results:
        d = Detection(activity_id=activity_id, kind="object", label=r["label"],
                      confidence=r["confidence"], lat=lat, lon=lon,
                      simulated=False, media_ref=dest.name)
        session.add(d)
        created.append(d)
    session.commit()
    for d in created:
        session.refresh(d)
    return {"created": len(created), "yolo_available": detect.has_yolo(), "detections": created}


@router.get("/activities/{activity_id}/detections")
def list_detections(activity_id: int, role: str = "organizer", session: Session = Depends(get_session)):
    _check_role(role)
    dets = session.exec(select(Detection).where(Detection.activity_id == activity_id)).all()
    if role == "protection":
        dets = [d for d in dets if d.status == "confirmed"]
    return dets


@router.post("/activities/{activity_id}/detections/change")
def change_detections(activity_id: int, body: ChangeIn, session: Session = Depends(get_session)):
    """Change detection (COD): simulate change points within a zone."""
    a = _get_activity(session, activity_id)
    zones = session.exec(
        select(Zone).where(Zone.activity_id == activity_id, Zone.kind == body.zone_kind)).all()
    if zones:
        ring = json.loads(zones[0].polygon_json)
    else:  # fall back to a box around the activity center
        c = 0.006
        ring = [[a.center_lon - c, a.center_lat - c], [a.center_lon + c, a.center_lat - c],
                [a.center_lon + c, a.center_lat + c], [a.center_lon - c, a.center_lat + c]]
    changes = detect.simulate_changes(ring, body.count, body.seed)
    created = []
    for c in changes:
        d = Detection(activity_id=activity_id, kind="change", label=c["label"],
                      confidence=c["confidence"], lat=c["lat"], lon=c["lon"], simulated=True)
        session.add(d)
        created.append(d)
        session.add(Event(activity_id=activity_id, type="change", role="search",
                          lat=c["lat"], lon=c["lon"], detail=f"change:{c['label']}"))
    session.commit()
    for d in created:
        session.refresh(d)
    return {"created": len(created), "detections": created}


@router.get("/activities/{activity_id}/events")
def list_events(activity_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(Event).where(Event.activity_id == activity_id).order_by(Event.ts)).all()


@router.post("/detections/{detection_id}/review")
def review_detection(detection_id: int, body: ReviewIn, session: Session = Depends(get_session)):
    d = session.get(Detection, detection_id)
    if not d:
        raise HTTPException(404, "detection not found")
    if body.status not in ("confirmed", "rejected", "candidate"):
        raise HTTPException(400, "invalid status")
    d.status = body.status
    if body.note is not None:
        d.note = body.note
    session.add(d)
    session.commit()
    session.refresh(d)
    return d


# ---- planning: coverage (protection) & route (organizer/search) -----------
def _no_go_polys(session: Session, activity_id: int) -> list[list[list[float]]]:
    zones = session.exec(select(Zone).where(Zone.activity_id == activity_id)).all()
    return [json.loads(z.polygon_json) for z in zones if z.kind == "no_go"]


@router.post("/activities/{activity_id}/coverage")
def coverage(activity_id: int, body: CoverageIn, session: Session = Depends(get_session)):
    a = _get_activity(session, activity_id)
    polygon = body.polygon
    if polygon is None and body.zone_id is not None:
        z = session.get(Zone, body.zone_id)
        if not z:
            raise HTTPException(404, "zone not found")
        polygon = json.loads(z.polygon_json)
    if not polygon:
        raise HTTPException(400, "provide zone_id or polygon")
    plan = geo.coverage_plan(polygon, a.center_lon, a.center_lat,
                             body.radius_m, body.spacing_m)
    plan["observation_points_geojson"] = _points_fc(
        plan["observation_points"], {"role": "protection", "type": "observation"})
    plan["gaps_geojson"] = _points_fc(plan["gaps"], {"role": "protection", "type": "gap"})
    return plan


@router.post("/activities/{activity_id}/route")
def route(activity_id: int, body: RouteIn, session: Session = Depends(get_session)):
    a = _get_activity(session, activity_id)
    no_go = _no_go_polys(session, activity_id)
    path = geo.astar(tuple(body.start), tuple(body.goal), no_go,
                     a.center_lon, a.center_lat, cell_m=body.cell_m)
    length = sum(geo.haversine_m(path[i], path[i + 1]) for i in range(len(path) - 1))
    return {
        "path": path,
        "length_m": round(length, 1),
        "avoided_no_go": len(no_go),
        "geojson": {"type": "Feature", "properties": {"length_m": round(length, 1)},
                    "geometry": {"type": "LineString", "coordinates": path}},
    }


# ---- aggregate state for the map ------------------------------------------
def _points_fc(points: list[list[float]], props: dict) -> dict:
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": props,
         "geometry": {"type": "Point", "coordinates": p}} for p in points]}


@router.get("/activities/{activity_id}/state")
def state(activity_id: int, role: str = "organizer", session: Session = Depends(get_session)):
    a = _get_activity(session, activity_id)
    _check_role(role)
    zones = list_zones(activity_id, role, session)
    tracks = list_tracks(activity_id, role, session)
    dets = list_detections(activity_id, role, session)

    zone_features = []
    for z in zones:
        ring = json.loads(z.polygon_json)
        if ring and ring[0] != ring[-1]:
            ring = ring + [ring[0]]
        zone_features.append({
            "type": "Feature",
            "properties": {"id": z.id, "name": z.name, "kind": z.kind, "role_owner": z.role_owner},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })

    track_features = []
    for t in tracks:
        pts = session.exec(
            select(TrackPoint).where(TrackPoint.track_id == t.id).order_by(TrackPoint.seq)
        ).all()
        coords = [[p.lon, p.lat] for p in pts]
        if len(coords) >= 2:
            track_features.append({
                "type": "Feature",
                "properties": {"id": t.id, "name": t.name, "team": t.team, "source": t.source},
                "geometry": {"type": "LineString", "coordinates": coords},
            })

    det_features = [{
        "type": "Feature",
        "properties": {"id": d.id, "label": d.label, "kind": d.kind, "confidence": d.confidence,
                       "status": d.status, "simulated": d.simulated, "note": d.note},
        "geometry": {"type": "Point", "coordinates": [d.lon, d.lat]},
    } for d in dets]

    return {
        "activity": a,
        "role": role,
        "zones": {"type": "FeatureCollection", "features": zone_features},
        "tracks": {"type": "FeatureCollection", "features": track_features},
        "detections": {"type": "FeatureCollection", "features": det_features},
        "counts": {"zones": len(zone_features), "tracks": len(track_features),
                   "detections": len(det_features),
                   "detections_simulated": sum(1 for d in dets if d.simulated),
                   "detections_real": sum(1 for d in dets if not d.simulated)},
    }


# ---- report ---------------------------------------------------------------
def _report_data(session: Session, activity_id: int):
    a = _get_activity(session, activity_id)
    zones = session.exec(select(Zone).where(Zone.activity_id == activity_id)).all()
    tracks = session.exec(select(Track).where(Track.activity_id == activity_id)).all()
    dets = session.exec(select(Detection).where(Detection.activity_id == activity_id)).all()
    return a, zones, tracks, dets


@router.get("/activities/{activity_id}/report.md", response_class=PlainTextResponse)
def report_md(activity_id: int, session: Session = Depends(get_session)):
    a, zones, tracks, dets = _report_data(session, activity_id)
    return report.build_markdown(a, zones, tracks, dets)


@router.get("/activities/{activity_id}/report.html", response_class=HTMLResponse)
def report_html(activity_id: int, session: Session = Depends(get_session)):
    a, zones, tracks, dets = _report_data(session, activity_id)
    md = report.build_markdown(a, zones, tracks, dets)
    return report.build_html(md, a.name)
