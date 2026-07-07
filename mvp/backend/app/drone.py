"""Simulated drone "aerial" view with super-resolution.

Two endpoints:
  * /drone-image  — a single super-res JPEG crop centered on a point.
  * /sr-tiles/{z}/{x}/{y}.jpg — a raster TILE service so the drone mini-map
    can pan/zoom continuously; beyond the native satellite zoom it synthesizes
    tiles by super-resolving the ancestor native tile.

Super-resolution uses a learned model (OpenCV dnn_superres, FSRCNN x4) when
available; otherwise it falls back to LANCZOS + unsharp. Honest note: SR
enhances/upscales existing imagery, it does not invent real new ground truth.
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
MODEL_DIR = DATA_STORE / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

_UA = "MSkitMVP/0.1"
_ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
_FSRCNN_URL = "https://raw.githubusercontent.com/Saafke/FSRCNN_Tensorflow/master/models/FSRCNN_x4.pb"
TILE = 256
NATIVE_MAX = 17          # native Esri zoom used as SR source; beyond -> synthesize
MAX_SYNTH = NATIVE_MAX + 2   # deepest zoom we serve (seamless x4 from ancestor)

_sr = None               # cached cv2 dnn_superres model (or False if unavailable)
_anc_cache: dict = {}    # (ax,ay,scale) -> upscaled ancestor PIL image


# ---- tiles ----------------------------------------------------------------
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
    try:
        req = urllib.request.Request(_ESRI.format(z=z, x=x, y=y), headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=7) as r:
            data = r.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return img
    except Exception:
        return None


# ---- super-resolution -----------------------------------------------------
def _load_sr():
    """Lazy-load OpenCV FSRCNN x4; download the model once. False if unavailable."""
    global _sr
    if _sr is not None:
        return _sr
    try:
        import cv2  # type: ignore
        model = MODEL_DIR / "FSRCNN_x4.pb"
        if not model.exists():
            req = urllib.request.Request(_FSRCNN_URL, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=15) as r:
                model.write_bytes(r.read())
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(str(model))
        sr.setModel("fsrcnn", 4)
        _sr = sr
    except Exception:
        _sr = False
    return _sr


def _sr_upscale(img: Image.Image, target: int) -> Image.Image:
    """Upscale a tile to target x target pixels (learned SR when available)."""
    sr = _load_sr()
    if sr:
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
            # cvtColor returns a C-contiguous array; a reversed-stride view
            # (arr[:,:,::-1]) makes dnn_superres emit streak/grid garbage.
            bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            up = sr.upsample(bgr)                                    # x4 (learned)
            out = Image.fromarray(cv2.cvtColor(up, cv2.COLOR_BGR2RGB))
            if out.size != (target, target):
                out = out.resize((target, target), Image.LANCZOS)
            return out.filter(ImageFilter.UnsharpMask(radius=1, percent=70, threshold=1))
        except Exception:
            pass
    big = img.resize((target, target), Image.LANCZOS)
    return big.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=2))


# ---- endpoints ------------------------------------------------------------
def _upscaled_ancestor(ax: int, ay: int, scale: int) -> Image.Image | None:
    """Upscale a whole native tile to 256*scale once (cached) so child tiles are
    seamless slices — avoids per-crop SR noise and tile-boundary grids."""
    key = (ax, ay, scale)
    if key in _anc_cache:
        return _anc_cache[key]
    anc = _fetch_tile(NATIVE_MAX, ax, ay)
    if anc is None:
        return None
    big = _sr_upscale(anc, TILE * scale)   # FSRCNN on a full 256 tile, then fit
    if len(_anc_cache) > 96:
        _anc_cache.clear()
    _anc_cache[key] = big
    return big


@router.get("/sr-tiles/{z}/{x}/{y}.jpg")
def sr_tile(z: int, x: int, y: int):
    """Raster tiles for the drone mini-map; SR-synthesized beyond native zoom."""
    if z > MAX_SYNTH:
        raise HTTPException(404, "beyond max zoom")
    if z <= NATIVE_MAX:
        img = _fetch_tile(z, x, y)
        if img is None:
            raise HTTPException(504, "tile unavailable")
    else:
        dz = z - NATIVE_MAX
        scale = 2 ** dz
        ax, ay = x >> dz, y >> dz
        big = _upscaled_ancestor(ax, ay, scale)
        if big is None:
            raise HTTPException(504, "tile unavailable")
        cx, cy = x - (ax << dz), y - (ay << dz)
        img = big.crop((cx * TILE, cy * TILE, cx * TILE + TILE, cy * TILE + TILE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return Response(buf.getvalue(), media_type="image/jpeg",
                    headers={"Cache-Control": "no-cache"})


@router.get("/drone-image")
def drone_image(lat: float = Query(...), lon: float = Query(...),
                z: int = Query(NATIVE_MAX), win: int = Query(360)):
    """Single super-res JPEG crop centered on (lat,lon)."""
    for zoom in range(min(z, NATIVE_MAX), 14, -1):
        xf, yf = _lonlat_to_tile(lon, lat, zoom)
        xi, yi = int(xf), int(yf)
        if _fetch_tile(zoom, xi, yi) is None:
            continue
        mosaic = Image.new("RGB", (TILE * 3, TILE * 3))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                t = _fetch_tile(zoom, xi + dx, yi + dy) or Image.new("RGB", (TILE, TILE), (20, 24, 32))
                mosaic.paste(t, ((dx + 1) * TILE, (dy + 1) * TILE))
        px, py = TILE + int((xf - xi) * TILE), TILE + int((yf - yi) * TILE)
        half = win // 2
        left = max(0, min(px - half, TILE * 3 - win))
        top = max(0, min(py - half, TILE * 3 - win))
        out = _sr_upscale(mosaic.crop((left, top, left + win, top + win)), win * 2)
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=88)
        return Response(buf.getvalue(), media_type="image/jpeg", headers={"X-Source-Zoom": str(zoom)})
    raise HTTPException(504, "no satellite tiles available")
