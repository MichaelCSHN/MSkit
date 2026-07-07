"""Raster tile cache — offline-resilient base map for the demo.

Serves /tiles/{z}/{x}/{y}.png from a local disk cache. On a cache miss it
tries to fetch once from OSM and stores it; after warming the demo area the
map keeps working without internet. A live pitch should pre-warm the venue
area (pan/zoom once online) so it survives a flaky connection.
"""
from __future__ import annotations

import urllib.request
from fastapi import APIRouter, Response, HTTPException

from .db import DATA_STORE

router = APIRouter()
TILE_DIR = DATA_STORE / "tiles"
TILE_DIR.mkdir(parents=True, exist_ok=True)

_UA = "MSkitMVP/0.1 (demo; offline-cache)"
_OSM = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


@router.get("/tiles/{z}/{x}/{y}.png")
def get_tile(z: int, x: int, y: int):
    if not (0 <= z <= 20 and 0 <= x < 2 ** z and 0 <= y < 2 ** z):
        raise HTTPException(400, "tile out of range")
    path = TILE_DIR / str(z) / str(x) / f"{y}.png"
    if path.exists():
        return Response(path.read_bytes(), media_type="image/png",
                        headers={"X-Tile-Cache": "hit"})
    # cache miss: try to warm from network (once)
    path.parent.mkdir(parents=True, exist_ok=True)
    url = _OSM.format(z=z, x=x, y=y)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = r.read()
        path.write_bytes(data)
        return Response(data, media_type="image/png", headers={"X-Tile-Cache": "warm"})
    except Exception:
        # offline and not cached
        raise HTTPException(504, "tile not cached and network unavailable")
