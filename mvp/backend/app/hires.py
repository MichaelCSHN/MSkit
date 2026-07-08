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

# NRW (Germany) rural / suburban — real 10 cm orthophotos (DOP), open data
# (Datenlizenz Deutschland Zero 2.0, ~public domain). The NRW DOP WMS reprojects
# from the native ETRS89/UTM32 (EPSG:25832) to WebMercator (EPSG:3857) on the
# fly, so MapLibre can consume it directly via a {bbox-epsg-3857} template — no
# key, no client-side reprojection. All of NRW is covered; regions below just
# pin the activity area to SAR-relevant rural terrain.
_NRW_DOP = (
    "https://www.wms.nrw.de/geobasis/wms_nw_dop?service=WMS&version=1.3.0"
    "&request=GetMap&layers=nw_dop_rgb&styles=&crs=EPSG:3857"
    "&bbox={bbox-epsg-3857}&width=256&height=256&format=image/jpeg"
)


def _nrw(rid, name, lon, lat):
    d = 0.010   # ~1 km half-box just for display bbox
    return {
        "id": rid, "name": name, "tms": _NRW_DOP,
        "bbox": [lon - d, lat - d, lon + d, lat + d], "center": [lon, lat],
        "gsd": 0.10, "maxzoom": 21, "src": "NRW DOP",
        "license": "DL-DE Zero 2.0", "provider": "Geobasis NRW",
    }


HIRES_REGIONS: list[dict] = [
    _nrw("nrw-eifel", "Eifel·Monschau 森林/村镇", 6.2536, 50.5548),
    _nrw("nrw-sauerland", "Sauerland·Winterberg 森林", 8.5306, 51.1951),
    _nrw("nrw-muensterland", "Münsterland·Billerbeck 农田", 7.2946, 51.9793),
    _nrw("nrw-eifelsee", "Eifel·Rursee 湖山", 6.4200, 50.6300),
]

_BY_ID = {r["id"]: r for r in HIRES_REGIONS}


@router.get("/hires-regions")
def hires_regions():
    """List available high-resolution real-imagery regions."""
    return HIRES_REGIONS


def region_by_id(rid: str):
    return _BY_ID.get(rid)
