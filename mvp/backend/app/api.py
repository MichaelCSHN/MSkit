"""HTTP API for the MVP tri-party platform."""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from .db import get_session
from .models import Activity, Zone, Track, TrackPoint, Detection, Event, Marker, ROLES
from . import geo
from .services import logparse, detect, report, sar

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
class ResetIn(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None


class RoadsIn(BaseModel):
    waypoints: list[list[float]]      # [[lon,lat], ...] >=2
    profile: str = "foot"            # foot (徒步) | car (机动车) | offroad (越野直连)


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


class PlaceTargetsIn(BaseModel):
    decoys: int = 4
    seed: int = 17


class DroneSweepIn(BaseModel):
    altitude_m: float = 80.0
    fov_deg: float = 60.0
    spacing_m: Optional[float] = None
    seed: int = 11


class PriorityIn(BaseModel):
    priority: int  # 1..5


class RoutePriorityIn(BaseModel):
    start: list[float]      # [lon,lat]
    min_priority: int = 1


class ArriveIn(BaseModel):
    point: list[float]      # [lon,lat]
    threshold_m: float = 60.0


# ---- health & activities --------------------------------------------------
@router.get("/health")
def health():
    return {"status": "ok", "yolo_available": detect.has_yolo()}


@router.post("/demo/reset")
def demo_reset(body: ResetIn | None = None, session: Session = Depends(get_session)):
    """Wipe all data and re-seed the demo activity (for repeatable pitches).
    Optional {lat,lon} centers the activity at the current location."""
    from sqlmodel import SQLModel
    from .db import engine
    from .seed import seed_if_empty, LAT0, LON0
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    lat = (body.lat if body and body.lat is not None else LAT0)
    lon = (body.lon if body and body.lon is not None else LON0)
    aid = seed_if_empty(lat, lon)
    return {"reset": True, "activity_id": aid, "center": [lon, lat]}


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


def _osrm_route(waypoints: list[list[float]]):
    """Car route via the public OSRM demo server (driving profile only)."""
    import urllib.request
    coords = ";".join(f"{p[0]},{p[1]}" for p in waypoints)
    url = (f"https://router.project-osrm.org/route/v1/driving/{coords}"
           f"?overview=full&geometries=geojson")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MSkitMVP/0.1"})
        with urllib.request.urlopen(req, timeout=7) as r:
            data = json.loads(r.read())
        if data.get("code") == "Ok" and data.get("routes"):
            rt = data["routes"][0]
            return rt["geometry"]["coordinates"], rt.get("distance")
    except Exception:
        pass
    return None, None


def _brouter_route(waypoints: list[list[float]], profile: str = "hiking-mountain"):
    """Walking/hiking route via BRouter (no API key). Returns ([lon,lat], dist)."""
    import urllib.request
    from urllib.parse import quote
    lonlats = quote("|".join(f"{p[0]},{p[1]}" for p in waypoints), safe=",")
    url = (f"https://brouter.de/brouter?lonlats={lonlats}"
           f"&profile={profile}&alternativeidx=0&format=geojson")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MSkitMVP/0.1"})
        with urllib.request.urlopen(req, timeout=9) as r:
            data = json.loads(r.read())
        feats = data.get("features")
        if feats:
            coords = [[c[0], c[1]] for c in feats[0]["geometry"]["coordinates"]]
            tl = feats[0].get("properties", {}).get("track-length")
            dist = float(tl) if tl else None
            if coords:
                return coords, dist
    except Exception:
        pass
    return None, None


@router.post("/activities/{activity_id}/route/roads")
def route_roads(activity_id: int, body: RoadsIn, session: Session = Depends(get_session)):
    """Multi-waypoint route. profile=foot (BRouter 徒步) / car (OSRM 机动车) /
    offroad (越野直连 A*). Any online failure falls back to offroad A* (avoids no-go)."""
    a = _get_activity(session, activity_id)
    wps = body.waypoints
    if len(wps) < 2:
        raise HTTPException(400, "need >= 2 waypoints")

    coords = dist = None
    used = "offroad"
    if body.profile == "foot":
        coords, dist = _brouter_route(wps)
        used = "foot"
    elif body.profile == "car":
        coords, dist = _osrm_route(wps)
        used = "car"

    if not coords:  # offroad, or online routing unavailable -> A* fallback
        no_go = _no_go_polys(session, activity_id)
        coords = [wps[0]]
        for i in range(len(wps) - 1):
            seg = geo.astar(tuple(wps[i]), tuple(wps[i + 1]), no_go, a.center_lon, a.center_lat)
            coords.extend(seg[1:])
        dist = None
        used = "offroad"

    length = dist if dist is not None else sum(
        geo.haversine_m(coords[i], coords[i + 1]) for i in range(len(coords) - 1))
    return {
        "profile": used,
        "roads": used in ("foot", "car"),
        "length_m": round(length, 1),
        "path": coords,
        "geojson": {"type": "Feature", "properties": {"length_m": round(length, 1)},
                    "geometry": {"type": "LineString", "coordinates": coords}},
    }


# ---- SAR (search & rescue) Phase 1 ----------------------------------------
def _search_ring(session: Session, activity_id: int):
    z = session.exec(select(Zone).where(Zone.activity_id == activity_id,
                                        Zone.kind == "search")).first()
    return json.loads(z.polygon_json) if z else None


@router.post("/demo/sar")
def demo_sar(body: ResetIn | None = None, session: Session = Depends(get_session)):
    """Reset to a fresh SAR scenario (organizer + search).
    Optional {lat,lon} centers it at the current location."""
    from sqlmodel import SQLModel
    from .db import engine
    from .seed import seed_sar, LAT0, LON0
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    lat = (body.lat if body and body.lat is not None else LAT0)
    lon = (body.lon if body and body.lon is not None else LON0)
    aid = seed_sar(lat, lon)
    return {"reset": True, "scenario": "sar", "activity_id": aid, "center": [lon, lat]}


@router.post("/activities/{activity_id}/sar/place-targets")
def sar_place_targets(activity_id: int, body: PlaceTargetsIn,
                      session: Session = Depends(get_session)):
    """Organizer places 1 hidden target + N decoys inside the search zone.
    Locations are NOT returned (hidden from the search team)."""
    a = _get_activity(session, activity_id)
    ring = _search_ring(session, activity_id)
    if not ring:
        raise HTTPException(400, "no search zone; draw one first")
    # clear previous hunt (markers + detections), reset completion
    for mk in session.exec(select(Marker).where(Marker.activity_id == activity_id)).all():
        session.delete(mk)
    for d in session.exec(select(Detection).where(Detection.activity_id == activity_id)).all():
        session.delete(d)
    a.sar_complete = False
    session.add(a)
    pts = geo.sample_in_ring(ring, body.decoys + 1, body.seed)
    if not pts:
        raise HTTPException(422, "could not sample points in search zone")
    for i, p in enumerate(pts):
        session.add(Marker(activity_id=activity_id, kind=("target" if i == 0 else "decoy"),
                           lon=p[0], lat=p[1]))
    session.commit()
    return {"placed": True, "target": 1, "decoys": len(pts) - 1}


@router.post("/activities/{activity_id}/sar/drone-sweep")
def sar_drone_sweep(activity_id: int, body: DroneSweepIn,
                    session: Session = Depends(get_session)):
    """Fly a lawnmower sweep of the search zone; probabilistically detect
    hidden markers within the camera footprint and surface them as candidates."""
    a = _get_activity(session, activity_id)
    ring = _search_ring(session, activity_id)
    if not ring:
        raise HTTPException(400, "no search zone")
    radius = sar.footprint_radius(body.altitude_m, body.fov_deg)
    spacing = body.spacing_m or radius * 1.6
    path = sar.lawnmower_path(ring, a.center_lon, a.center_lat, spacing)
    cov = sar.coverage_ratio(ring, path, radius, a.center_lon, a.center_lat)
    markers = session.exec(select(Marker).where(Marker.activity_id == activity_id,
                                                Marker.revealed == False)).all()  # noqa: E712
    hits = sar.detect_markers(path, markers, radius, body.seed)
    created = 0
    mk_by_id = {m.id: m for m in markers}
    for h in hits:
        d = Detection(activity_id=activity_id, kind="object", label=h["label"],
                      confidence=h["confidence"], priority=h["priority"],
                      lat=h["lat"], lon=h["lon"], simulated=True)
        session.add(d)
        session.commit()
        session.refresh(d)
        mk = mk_by_id.get(h["marker_id"])
        if mk:
            mk.revealed = True
            mk.detection_id = d.id
            session.add(mk)
        session.add(Event(activity_id=activity_id, type="detection", role="search",
                          lat=h["lat"], lon=h["lon"], detail=f"drone:{h['label']} p{h['priority']}"))
        created += 1
    session.commit()
    return {
        "footprint_m": round(radius, 1), "spacing_m": round(spacing, 1),
        "coverage_ratio": cov, "detected": created,
        "sweep": {"type": "Feature", "properties": {"coverage": cov},
                  "geometry": {"type": "LineString", "coordinates": path}},
    }


@router.post("/detections/{detection_id}/priority")
def set_priority(detection_id: int, body: PriorityIn, session: Session = Depends(get_session)):
    d = session.get(Detection, detection_id)
    if not d:
        raise HTTPException(404, "detection not found")
    d.priority = max(1, min(5, body.priority))
    session.add(d)
    session.commit()
    session.refresh(d)
    return d


@router.post("/activities/{activity_id}/sar/route-priority")
def sar_route_priority(activity_id: int, body: RoutePriorityIn,
                       session: Session = Depends(get_session)):
    """Greedy priority tour from `start` through candidate detections."""
    a = _get_activity(session, activity_id)
    dets = session.exec(select(Detection).where(Detection.activity_id == activity_id)).all()
    pts = [{"id": d.id, "lat": d.lat, "lon": d.lon, "priority": d.priority}
           for d in dets if d.status != "rejected" and d.priority >= body.min_priority]
    if not pts:
        raise HTTPException(422, "no candidate points at/above min_priority")
    tour = sar.priority_tour(body.start, pts, _no_go_polys(session, activity_id),
                             a.center_lon, a.center_lat)
    tour["geojson"] = {"type": "Feature", "properties": {"length_m": tour["length_m"]},
                       "geometry": {"type": "LineString", "coordinates": tour["path"]}}
    tour["stops"] = len(pts)
    return tour


@router.post("/activities/{activity_id}/sar/arrive")
def sar_arrive(activity_id: int, body: ArriveIn, session: Session = Depends(get_session)):
    """Check whether `point` reaches the hidden target; mark complete if so."""
    a = _get_activity(session, activity_id)
    target = session.exec(select(Marker).where(Marker.activity_id == activity_id,
                                               Marker.kind == "target")).first()
    if not target:
        raise HTTPException(400, "no target placed")
    dist = geo.haversine_m(body.point, [target.lon, target.lat])
    arrived = dist <= body.threshold_m
    if arrived:
        a.sar_complete = True
        session.add(a)
        session.commit()
    return {"arrived": arrived, "complete": a.sar_complete, "distance_m": round(dist, 1),
            "threshold_m": body.threshold_m}


@router.get("/activities/{activity_id}/sar/status")
def sar_status(activity_id: int, session: Session = Depends(get_session)):
    a = _get_activity(session, activity_id)
    markers = session.exec(select(Marker).where(Marker.activity_id == activity_id)).all()
    target = next((m for m in markers if m.kind == "target"), None)
    decoys = [m for m in markers if m.kind == "decoy"]
    return {
        "scenario": a.scenario, "has_target": target is not None,
        "target_revealed": bool(target and target.revealed),
        "decoys": len(decoys), "decoys_revealed": sum(1 for m in decoys if m.revealed),
        "complete": a.sar_complete,
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
                       "priority": d.priority, "status": d.status, "simulated": d.simulated,
                       "note": d.note},
        "geometry": {"type": "Point", "coordinates": [d.lon, d.lat]},
    } for d in dets]

    # SAR ground-truth markers (target/decoys): visible to organizer only.
    # The search role sees them only indirectly, as drone-detected candidates.
    marker_rows = (session.exec(select(Marker).where(Marker.activity_id == activity_id)).all()
                   if role == "organizer" else [])
    marker_features = [{
        "type": "Feature",
        "properties": {"id": mk.id, "kind": mk.kind, "revealed": mk.revealed},
        "geometry": {"type": "Point", "coordinates": [mk.lon, mk.lat]},
    } for mk in marker_rows]

    return {
        "activity": a,
        "role": role,
        "zones": {"type": "FeatureCollection", "features": zone_features},
        "tracks": {"type": "FeatureCollection", "features": track_features},
        "detections": {"type": "FeatureCollection", "features": det_features},
        "markers": {"type": "FeatureCollection", "features": marker_features},
        "counts": {"zones": len(zone_features), "tracks": len(track_features),
                   "detections": len(det_features), "markers": len(marker_features),
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
