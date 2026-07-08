"""High-resolution real-imagery regions (OpenAerialMap).

Registry of openly-licensed (CC-BY 4.0) UAV orthophoto tilesets. Selecting a
region constrains the MVP's activity area to where real cm-level imagery exists,
so the drone "aerial view" can image REAL orthophotos along the sweep path
instead of upscaled satellite tiles.

Source: OpenAerialMap / Open Imagery Network. Each region is one published UAV
ortho with a ready TMS endpoint and a known bbox (real-world georeferenced).
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# Chattogram, Bangladesh — GPAD UAV survey, 3–3.5 cm GSD, CC-BY 4.0.
# tms/bbox/center pulled verbatim from the OAM metadata API.
HIRES_REGIONS = [
    {
        "id": "chattogram-14",
        "name": "Chattogram 城区 14",
        "tms": "https://tiles.openaerialmap.org/6a1eb61093c47b7abc1c2069/0/6a1eb61093c47b7abc1c206a/{z}/{x}/{y}",
        "bbox": [91.766293, 22.370283, 91.789695, 22.381298],
        "center": [91.778, 22.3758],
        "gsd": 0.030, "maxzoom": 22,
        "license": "CC-BY 4.0", "provider": "GPAD via OpenAerialMap",
    },
    {
        "id": "chattogram-06",
        "name": "Chattogram 城区 06",
        "tms": "https://tiles.openaerialmap.org/6a1e997f93c47b7abc1be4c1/0/6a1e997f93c47b7abc1be4c2/{z}/{x}/{y}",
        "bbox": [91.808609, 22.424797, 91.8242, 22.435749],
        "center": [91.8164, 22.4303],
        "gsd": 0.035, "maxzoom": 22,
        "license": "CC-BY 4.0", "provider": "GPAD via OpenAerialMap",
    },
    {
        "id": "chattogram-18",
        "name": "Chattogram 城区 18",
        "tms": "https://tiles.openaerialmap.org/6a255496f6c7e0f5d490f977/0/6a255496f6c7e0f5d490f978/{z}/{x}/{y}",
        "bbox": [91.812675, 22.413987, 91.835949, 22.424995],
        "center": [91.8243, 22.4195],
        "gsd": 0.035, "maxzoom": 22,
        "license": "CC-BY 4.0", "provider": "GPAD via OpenAerialMap",
    },
    {
        "id": "chattogram-02",
        "name": "Chattogram 河岸 02",
        "tms": "https://tiles.openaerialmap.org/6a41e742b27aa6a12ba6ca75/0/6a41e742b27aa6a12ba6ca76/{z}/{x}/{y}",
        "bbox": [91.788944, 22.446329, 91.804691, 22.457284],
        "center": [91.7968, 22.4518],
        "gsd": 0.035, "maxzoom": 22,
        "license": "CC-BY 4.0", "provider": "GPAD via OpenAerialMap",
    },
    {
        "id": "chattogram-30",
        "name": "Chattogram 城郊 30",
        "tms": "https://tiles.openaerialmap.org/6a2692932b10ed16a4aafa3d/0/6a2692932b10ed16a4aafa3e/{z}/{x}/{y}",
        "bbox": [91.766579, 22.337768, 91.778326, 22.348695],
        "center": [91.7724, 22.3432],
        "gsd": 0.035, "maxzoom": 22,
        "license": "CC-BY 4.0", "provider": "GPAD via OpenAerialMap",
    },
    {
        "id": "chattogram-45",
        "name": "Chattogram 南郊 45",
        "tms": "https://tiles.openaerialmap.org/6a4216a6b27aa6a12ba6ea79/0/6a4216a6b27aa6a12ba6ea7a/{z}/{x}/{y}",
        "bbox": [91.778891, 22.261986, 91.799016, 22.272974],
        "center": [91.7890, 22.2675],
        "gsd": 0.035, "maxzoom": 22,
        "license": "CC-BY 4.0", "provider": "GPAD via OpenAerialMap",
    },
]

_BY_ID = {r["id"]: r for r in HIRES_REGIONS}


@router.get("/hires-regions")
def hires_regions():
    """List available high-resolution real-imagery regions."""
    return HIRES_REGIONS


def region_by_id(rid: str):
    return _BY_ID.get(rid)
