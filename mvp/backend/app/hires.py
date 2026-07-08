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

# Chattogram (OAM) removed — pivoted to NRW.
# NRW 3D-Mesh (open, DL-DE Zero 2.0) is served as a live 3D flythrough via the
# standalone deck.gl + I3S page (frontend/nrw3d.html), NOT as a nadir TMS here.
# To restore a real nadir layer over NRW later, add NRW DOP (10cm orthophoto)
# WMTS/XYZ entries below.
HIRES_REGIONS: list[dict] = []

_BY_ID = {r["id"]: r for r in HIRES_REGIONS}


@router.get("/hires-regions")
def hires_regions():
    """List available high-resolution real-imagery regions."""
    return HIRES_REGIONS


def region_by_id(rid: str):
    return _BY_ID.get(rid)
