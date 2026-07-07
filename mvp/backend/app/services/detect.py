"""Search-side detection.

Two modes:
  * REAL: run an object detector (Ultralytics YOLO) on an image if installed.
    NOTE: YOLO/Ultralytics is AGPL-3.0 — for a commercial build a license
    decision is required (see docs). MVP demo use only.
  * SIMULATED: place pseudo-detections along a track for a stable demo.
    Always flagged simulated=True so the UI/report can disclose honestly
    (see MVP_Demo_Plan §10 "real vs simulated").
"""
from __future__ import annotations

from typing import Optional

# COCO -> civilian class mapping
_COCO_CIVIL = {
    "person": "person",
    "car": "vehicle", "truck": "vehicle", "bus": "vehicle", "motorcycle": "vehicle",
    "bicycle": "vehicle", "boat": "vehicle", "airplane": "vehicle",
    "dog": "animal", "cat": "animal", "horse": "animal", "sheep": "animal",
    "cow": "animal", "bird": "animal", "bear": "animal",
}


def _yolo_model():
    """Lazy-load a YOLO model; return None if ultralytics is not installed."""
    try:
        from ultralytics import YOLO  # type: ignore
    except Exception:
        return None
    global _MODEL
    try:
        _MODEL  # type: ignore[name-defined]
    except NameError:
        _MODEL = YOLO("yolov8n.pt")  # downloads on first use
    return _MODEL


def has_yolo() -> bool:
    try:
        import ultralytics  # noqa: F401
        return True
    except Exception:
        return False


def detect_image(path: str, conf: float = 0.35) -> list[dict]:
    """Run real detection on an image. Returns [{cls, confidence}] (civilian classes).

    Empty list if YOLO unavailable — caller should fall back to simulated.
    """
    model = _yolo_model()
    if model is None:
        return []
    try:
        results = model.predict(path, conf=conf, verbose=False)
    except Exception:
        return []
    out: list[dict] = []
    for r in results:
        names = r.names
        for b in r.boxes:
            raw = names.get(int(b.cls), str(int(b.cls)))
            cls = _COCO_CIVIL.get(raw)
            if not cls:
                continue
            out.append({"label": cls, "confidence": round(float(b.conf), 3), "simulated": False})
    return out


def _lcg(seed: int):
    x = seed & 0x7FFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x / 0x7FFFFFFF


def simulate_along_track(points: list[dict], classes: Optional[list[str]] = None,
                         count: int = 6, seed: int = 42) -> list[dict]:
    """Place `count` pseudo-detections near a track for a stable demo."""
    classes = classes or ["person", "vehicle", "animal"]
    if not points:
        return []
    rng = _lcg(seed)
    out: list[dict] = []
    n = len(points)
    for i in range(count):
        p = points[int(next(rng) * (n - 1))]
        # jitter ~ up to ~0.0009 deg (~100m) offset
        dlat = (next(rng) - 0.5) * 0.0018
        dlon = (next(rng) - 0.5) * 0.0018
        label = classes[int(next(rng) * len(classes)) % len(classes)]
        out.append({
            "label": label,
            "confidence": round(0.55 + next(rng) * 0.4, 3),
            "lat": round(p["lat"] + dlat, 6),
            "lon": round(p["lon"] + dlon, 6),
            "simulated": True,
        })
    return out
