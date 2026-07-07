"""Search-and-rescue (SAR) Phase-1 logic.

Simulates a drone lawnmower sweep of the search zone and probabilistic
detection of hidden ground-truth markers (1 target + N decoys). No real
imagery — the "drone view" is a satellite-tile crop on the frontend.
"""
from __future__ import annotations

import math
from .. import geo


def footprint_radius(altitude_m: float, fov_deg: float) -> float:
    """Ground radius seen by the camera = altitude * tan(fov/2)."""
    return max(10.0, altitude_m * math.tan(math.radians(fov_deg / 2)))


def priority_from_conf(conf: float) -> int:
    return max(1, min(5, round(conf * 5)))


def _rng(seed: int):
    x = seed & 0x7FFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x / 0x7FFFFFFF


def lawnmower_path(ring: list[list[float]], c_lon: float, c_lat: float,
                   spacing_m: float) -> list[list[float]]:
    """Boustrophedon sweep across the zone bbox; returns [lon,lat] points."""
    if len(ring) < 3:
        return []
    minx, miny, maxx, maxy = geo.bbox(ring)
    x0, y0 = geo.to_xy(minx, miny, c_lon, c_lat)
    x1, y1 = geo.to_xy(maxx, maxy, c_lon, c_lat)
    step = max(spacing_m, 20.0)
    sample = step / 2.0
    path: list[list[float]] = []
    y = y0
    up = True
    while y <= y1:
        xs = []
        x = x0
        while x <= x1:
            xs.append(x)
            x += sample
        if not up:
            xs.reverse()
        for xx in xs:
            lon, lat = geo.to_lonlat(xx, y, c_lon, c_lat)
            path.append([round(lon, 6), round(lat, 6)])
        y += step
        up = not up
    return path


def coverage_ratio(ring: list[list[float]], path: list[list[float]],
                   radius_m: float, c_lon: float, c_lat: float) -> float:
    if len(ring) < 3 or not path:
        return 0.0
    path_xy = [geo.to_xy(p[0], p[1], c_lon, c_lat) for p in path]
    minx, miny, maxx, maxy = geo.bbox(ring)
    sx0, sy0 = geo.to_xy(minx, miny, c_lon, c_lat)
    sx1, sy1 = geo.to_xy(maxx, maxy, c_lon, c_lat)
    cell = max(radius_m, 25.0)
    total = covered = 0
    r2 = radius_m ** 2
    y = sy0
    while y <= sy1:
        x = sx0
        while x <= sx1:
            lon, lat = geo.to_lonlat(x, y, c_lon, c_lat)
            if geo.point_in_ring((lon, lat), ring):
                total += 1
                if any((x - px) ** 2 + (y - py) ** 2 <= r2 for px, py in path_xy):
                    covered += 1
            x += cell
        y += cell
    return round(covered / total, 3) if total else 0.0


def detect_markers(path: list[list[float]], markers: list, radius_m: float,
                   seed: int = 11) -> list[dict]:
    """For each marker whose position is within footprint of any path point,
    roll a detection. Target => higher confidence; decoy => medium.

    Returns [{marker_id, kind, label, confidence, priority, lat, lon}].
    """
    rng = _rng(seed)
    out: list[dict] = []
    for mk in markers:
        seen = any(geo.haversine_m([mk.lon, mk.lat], p) <= radius_m for p in path)
        if not seen:
            continue
        # Both target and decoys surface as generic "candidate"s — the target
        # only trends higher-confidence; the team must verify by reaching it.
        if mk.kind == "target":
            conf = round(0.70 + next(rng) * 0.25, 3)
        else:
            conf = round(0.40 + next(rng) * 0.35, 3)
        label = "candidate"
        # detected position carries small localization noise
        dlat = (next(rng) - 0.5) * 0.0004
        dlon = (next(rng) - 0.5) * 0.0004
        out.append({
            "marker_id": mk.id, "kind": mk.kind, "label": label,
            "confidence": conf, "priority": priority_from_conf(conf),
            "lat": round(mk.lat + dlat, 6), "lon": round(mk.lon + dlon, 6),
        })
    return out


def priority_tour(start: list[float], points: list[dict], no_go, c_lon, c_lat):
    """Greedy nearest-neighbour tour from `start` through candidate points,
    breaking ties toward higher priority. Path segments avoid no-go zones.

    `points`: [{id, lat, lon, priority}]. Returns {path, order, length_m}.
    """
    remaining = list(points)
    cur = list(start)
    full_path = [list(start)]
    order = []
    total = 0.0
    while remaining:
        # score = distance discounted by priority (prefer near + high priority)
        def cost(p):
            d = geo.haversine_m(cur, [p["lon"], p["lat"]])
            return d / (1.0 + 0.15 * (p.get("priority", 1)))
        nxt = min(remaining, key=cost)
        seg = geo.astar(tuple(cur), (nxt["lon"], nxt["lat"]), no_go, c_lon, c_lat)
        if len(seg) > 1:
            full_path.extend(seg[1:])
            total += sum(geo.haversine_m(seg[i], seg[i + 1]) for i in range(len(seg) - 1))
        cur = [nxt["lon"], nxt["lat"]]
        order.append(nxt["id"])
        remaining.remove(nxt)
    return {"path": full_path, "order": order, "length_m": round(total, 1)}
