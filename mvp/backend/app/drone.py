"""Simulated drone "aerial" image with super-resolution enhancement.

Fetches the best native-zoom Esri satellite tiles around a point, crops a
window centered on it, then upscales 2x with LANCZOS + unsharp masking.
Honest note: this ENHANCES existing imagery (sharper/larger), it does not
synthesize real new ground detail. A learned SR model (Real-ESRGAN) can be
swapped into `_enhance` later.
"""
from __future__ import annotations

import io
import math
import urllib.request

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from PIL import Image, ImageFilter

from .db import DATA_STORE

router = APIRouter()
ESRI_DIR = DATA_STORE / "esri"
ESRI_DIR.mkdir(parents=True, exist_ok=True)
_UA = "MSkitMVP/0.1"
_ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
TILE = 256


def _lonlat_to_tile(lon: float, lat: float, z: int) -> tuple[float, float]:
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    latr = math.radians(lat)
    y = (1.0 - math.log(math.tan(latr) + 1.0 / math.cos(latr)) / math.pi) / 2.0 * n
    return x, y


def _fetch_tile(z: int, x: int, y: int) -> Image.Image | None:
    path = ESRI_DIR / str(z) / str(x) / f"{y}.jpg"
    if path.exists():
        try:
            return Image.open(path).convert("RGB")
        except Exception:
            pass
    url = _ESRI.format(z=z, x=x, y=y)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=7) as r:
            data = r.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return img
    except Exception:
        return None


def _enhance(img: Image.Image, scale: int = 2) -> Image.Image:
    big = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    return big.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))


@router.get("/drone-image")
def drone_image(lat: float = Query(...), lon: float = Query(...),
                z: int = Query(17), win: int = Query(360)):
    """Return a super-res JPEG aerial crop centered on (lat,lon).
    Tries zoom z downward until native tiles exist."""
    for zoom in range(min(z, 19), 14, -1):
        xf, yf = _lonlat_to_tile(lon, lat, zoom)
        xi, yi = int(xf), int(yf)
        center = _fetch_tile(zoom, xi, yi)
        if center is None:
            continue
        # stitch 3x3 mosaic for context
        mosaic = Image.new("RGB", (TILE * 3, TILE * 3))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                t = _fetch_tile(zoom, xi + dx, yi + dy) or Image.new("RGB", (TILE, TILE), (20, 24, 32))
                mosaic.paste(t, ((dx + 1) * TILE, (dy + 1) * TILE))
        # exact point pixel inside the mosaic (center tile is the middle one)
        px = TILE + int((xf - xi) * TILE)
        py = TILE + int((yf - yi) * TILE)
        half = win // 2
        left = max(0, min(px - half, TILE * 3 - win))
        top = max(0, min(py - half, TILE * 3 - win))
        crop = mosaic.crop((left, top, left + win, top + win))
        out = _enhance(crop, scale=2)
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=88)
        return Response(buf.getvalue(), media_type="image/jpeg",
                        headers={"X-Source-Zoom": str(zoom)})
    raise HTTPException(504, "no satellite tiles available / unreachable")
