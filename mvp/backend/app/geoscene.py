"""GeoScene: geo-plausible 3D from open data (Level 0/1).

Not photogrammetry — "position from the map, colour from the orthophoto, shape
from rules". This module supplies the *vector* geometry (OSM via Overpass) that
the frontend extrudes/fills on top of DEM terrain + orthophoto drape:

  * buildings  -> footprint + height  -> fill-extrusion (LOD1)
  * wood       -> canopy polygons     -> fill-extrusion (~16 m) as trees
  * water      -> polygons            -> flat blue fill
  * farmland/meadow/grass -> polygons -> flat coloured fill

Results are cached to disk (offline-first): once an AOI is fetched online it
works offline afterwards.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

from fastapi import APIRouter, HTTPException, Query

from .db import DATA_STORE

router = APIRouter()
CACHE = DATA_STORE / "geoscene"
CACHE.mkdir(parents=True, exist_ok=True)

_OVERPASS = "https://overpass-api.de/api/interpreter"
_UA = "MSkitMVP/0.1 (geoscene)"
_MAX_FEATURES = 6000


def _height(tags: dict) -> float:
    h = tags.get("height") or tags.get("building:height")
    if h:
        m = re.search(r"[0-9]+(\.[0-9]+)?", h)
        if m:
            return max(2.0, float(m.group(0)))
    lv = tags.get("building:levels")
    if lv:
        try:
            return max(3.0, float(re.sub(r"[^0-9.]", "", lv)) * 3.2)
        except ValueError:
            pass
    return 6.0


def _classify(tags: dict) -> str | None:
    if "building" in tags:
        return "building"
    if tags.get("natural") == "wood" or tags.get("landuse") == "forest":
        return "wood"
    if tags.get("natural") == "water" or "water" in tags or tags.get("waterway"):
        return "water"
    if tags.get("landuse") == "farmland":
        return "farmland"
    if tags.get("landuse") in ("meadow", "grass") or tags.get("natural") == "grassland":
        return "grass"
    return None


def _query(s: float, w: float, n: float, e: float) -> str:
    bb = f"{s},{w},{n},{e}"
    return (
        "[out:json][timeout:25];("
        f'way["building"]({bb});'
        f'way["natural"="wood"]({bb});way["landuse"="forest"]({bb});'
        f'way["natural"="water"]({bb});way["landuse"="reservoir"]({bb});'
        f'way["landuse"="farmland"]({bb});'
        f'way["landuse"="meadow"]({bb});way["landuse"="grass"]({bb});'
        f'way["natural"="grassland"]({bb});'
        ");out geom;"
    )


def _to_features(elements: list) -> list:
    feats = []
    for el in elements:
        if el.get("type") != "way":
            continue
        geom = el.get("geometry")
        if not geom or len(geom) < 4:
            continue
        kind = _classify(el.get("tags", {}))
        if not kind:
            continue
        ring = [[round(p["lon"], 6), round(p["lat"], 6)] for p in geom]
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        props = {"kind": kind}
        if kind == "building":
            props["height"] = _height(el.get("tags", {}))
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": props,
        })
        if len(feats) >= _MAX_FEATURES:
            break
    return feats


@router.get("/geoscene/features")
def geoscene_features(
    w: float = Query(...), s: float = Query(...),
    e: float = Query(...), n: float = Query(...),
):
    """OSM footprints/landcover in the bbox as GeoJSON (cached to disk)."""
    key = f"{w:.4f}_{s:.4f}_{e:.4f}_{n:.4f}.json"
    path = CACHE / key
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    try:
        data = urllib.parse.urlencode({"data": _query(s, w, n, e)}).encode()
        req = urllib.request.Request(_OVERPASS, data=data, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=40) as r:
            payload = json.loads(r.read())
    except Exception as err:
        # graceful: empty scene + note, so the UI still works offline / on failure
        return {"type": "FeatureCollection", "features": [],
                "note": f"overpass unavailable: {err}"}
    fc = {"type": "FeatureCollection", "features": _to_features(payload.get("elements", []))}
    counts: dict = {}
    for f in fc["features"]:
        counts[f["properties"]["kind"]] = counts.get(f["properties"]["kind"], 0) + 1
    fc["counts"] = counts
    try:
        path.write_text(json.dumps(fc), encoding="utf-8")
    except Exception:
        pass
    return fc
