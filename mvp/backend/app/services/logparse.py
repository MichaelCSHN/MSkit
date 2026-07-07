"""Parse drone / team flight logs into track points.

Supported: GPX (<trkpt>), CSV (lat/lon[/ele/time] columns, order-flexible).
No external deps. Returns list of dicts: {seq, lat, lon, ele, ts}.
"""
from __future__ import annotations

import csv
import io
import re
import xml.etree.ElementTree as ET
from datetime import datetime


def _parse_ts(val: str | None):
    if not val:
        return None
    val = val.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    # epoch seconds?
    if re.fullmatch(r"\d{9,13}", val):
        try:
            return datetime.utcfromtimestamp(int(val[:10]))
        except (ValueError, OverflowError):
            return None
    return None


def parse_gpx(text: str) -> list[dict]:
    points: list[dict] = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return points
    # strip namespaces
    ns = re.match(r"\{.*\}", root.tag)
    prefix = ns.group(0) if ns else ""
    seq = 0
    for pt in root.iter(f"{prefix}trkpt"):
        lat = pt.get("lat")
        lon = pt.get("lon")
        if lat is None or lon is None:
            continue
        ele_el = pt.find(f"{prefix}ele")
        time_el = pt.find(f"{prefix}time")
        points.append({
            "seq": seq,
            "lat": float(lat),
            "lon": float(lon),
            "ele": float(ele_el.text) if ele_el is not None and ele_el.text else None,
            "ts": _parse_ts(time_el.text) if time_el is not None else None,
        })
        seq += 1
    return points


def parse_csv(text: str) -> list[dict]:
    points: list[dict] = []
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return points
    # map flexible header names
    cols = {c.lower().strip(): c for c in reader.fieldnames}

    def pick(*names):
        for n in names:
            if n in cols:
                return cols[n]
        return None

    lat_c = pick("lat", "latitude", "y")
    lon_c = pick("lon", "lng", "longitude", "x")
    ele_c = pick("ele", "alt", "altitude", "elevation", "height")
    ts_c = pick("ts", "time", "timestamp", "datetime")
    if not lat_c or not lon_c:
        return points
    seq = 0
    for row in reader:
        try:
            lat = float(row[lat_c])
            lon = float(row[lon_c])
        except (TypeError, ValueError):
            continue
        ele = None
        if ele_c and row.get(ele_c):
            try:
                ele = float(row[ele_c])
            except ValueError:
                ele = None
        points.append({
            "seq": seq, "lat": lat, "lon": lon, "ele": ele,
            "ts": _parse_ts(row.get(ts_c) if ts_c else None),
        })
        seq += 1
    return points


def parse_log(filename: str, text: str) -> list[dict]:
    name = (filename or "").lower()
    if name.endswith(".gpx") or "<gpx" in text[:200].lower():
        return parse_gpx(text)
    return parse_csv(text)
