"""Lightweight geometry helpers (no external deps).

Coordinates are [lon, lat] (GeoJSON order). Planning uses a local
equirectangular projection to meters around an activity center.
"""
from __future__ import annotations

import heapq
import math
from typing import Iterable

EARTH_R = 6371000.0  # meters


def meters_per_deg(lat: float) -> tuple[float, float]:
    """Return (m per deg lon, m per deg lat) at a latitude."""
    lat_rad = math.radians(lat)
    m_lat = 111132.92 - 559.82 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
    m_lon = 111412.84 * math.cos(lat_rad) - 93.5 * math.cos(3 * lat_rad)
    return m_lon, m_lat


def to_xy(lon: float, lat: float, c_lon: float, c_lat: float) -> tuple[float, float]:
    m_lon, m_lat = meters_per_deg(c_lat)
    return (lon - c_lon) * m_lon, (lat - c_lat) * m_lat


def to_lonlat(x: float, y: float, c_lon: float, c_lat: float) -> tuple[float, float]:
    m_lon, m_lat = meters_per_deg(c_lat)
    return c_lon + x / m_lon, c_lat + y / m_lat


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distance in meters between [lon,lat] points."""
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dlon, dlat = lon2 - lon1, lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(h))


def point_in_ring(pt: tuple[float, float], ring: list[list[float]]) -> bool:
    """Ray-casting point-in-polygon. pt=[lon,lat], ring=[[lon,lat],...]."""
    if len(ring) < 3:
        return False
    x, y = pt
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-18) + xi):
            inside = not inside
        j = i
    return inside


def bbox(ring: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def astar(start: tuple[float, float], goal: tuple[float, float],
          no_go: list[list[list[float]]], c_lon: float, c_lat: float,
          cell_m: float = 20.0, margin_m: float = 200.0) -> list[list[float]]:
    """Grid A* from start to goal ([lon,lat]) avoiding no-go polygons.

    Returns a path as a list of [lon,lat]. Falls back to a straight line
    if no grid path is found.
    """
    sx, sy = to_xy(start[0], start[1], c_lon, c_lat)
    gx, gy = to_xy(goal[0], goal[1], c_lon, c_lat)
    minx, maxx = min(sx, gx) - margin_m, max(sx, gx) + margin_m
    miny, maxy = min(sy, gy) - margin_m, max(sy, gy) + margin_m

    def blocked(x: float, y: float) -> bool:
        lon, lat = to_lonlat(x, y, c_lon, c_lat)
        return any(point_in_ring((lon, lat), poly) for poly in no_go)

    def node(x: float, y: float) -> tuple[int, int]:
        return round((x - minx) / cell_m), round((y - miny) / cell_m)

    start_n, goal_n = node(sx, sy), node(gx, gy)

    def xy(n: tuple[int, int]) -> tuple[float, float]:
        return minx + n[0] * cell_m, miny + n[1] * cell_m

    def h(n: tuple[int, int]) -> float:
        ax, ay = xy(n)
        return math.hypot(ax - gx, ay - gy)

    open_heap: list[tuple[float, tuple[int, int]]] = [(0.0, start_n)]
    came: dict[tuple[int, int], tuple[int, int]] = {}
    g: dict[tuple[int, int], float] = {start_n: 0.0}
    nx_max = int((maxx - minx) / cell_m) + 1
    ny_max = int((maxy - miny) / cell_m) + 1
    seen = 0
    while open_heap and seen < 60000:
        _, cur = heapq.heappop(open_heap)
        seen += 1
        if cur == goal_n:
            break
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nb = (cur[0] + dx, cur[1] + dy)
                if not (0 <= nb[0] <= nx_max and 0 <= nb[1] <= ny_max):
                    continue
                bx, by = xy(nb)
                if blocked(bx, by):
                    continue
                step = cell_m * (1.4142 if dx and dy else 1.0)
                ng = g[cur] + step
                if ng < g.get(nb, float("inf")):
                    g[nb] = ng
                    came[nb] = cur
                    heapq.heappush(open_heap, (ng + h(nb), nb))

    if goal_n not in came and goal_n != start_n:
        return [list(start), list(goal)]  # fallback straight line

    path_nodes = [goal_n]
    cur = goal_n
    while cur != start_n and cur in came:
        cur = came[cur]
        path_nodes.append(cur)
    path_nodes.reverse()
    out = []
    for n in path_nodes:
        px, py = xy(n)
        lon, lat = to_lonlat(px, py, c_lon, c_lat)
        out.append([round(lon, 6), round(lat, 6)])
    return out


def coverage_plan(zone: list[list[float]], c_lon: float, c_lat: float,
                  radius_m: float = 120.0, spacing_m: float = 150.0):
    """Protection-side coverage planning over a zone polygon.

    Places observation points on a grid inside the zone, computes covered
    grid cells (within radius of any obs point) vs total, returns obs points,
    coverage ratio and gap cell centers. All returned coords are [lon,lat].
    """
    if len(zone) < 3:
        return {"observation_points": [], "coverage_ratio": 0.0, "gaps": [], "cells_total": 0}
    minx, miny, maxx, maxy = bbox(zone)
    # sample grid in projected meters
    sx0, sy0 = to_xy(minx, miny, c_lon, c_lat)
    sx1, sy1 = to_xy(maxx, maxy, c_lon, c_lat)
    step = spacing_m
    obs_xy: list[tuple[float, float]] = []
    y = sy0
    while y <= sy1:
        x = sx0
        while x <= sx1:
            lon, lat = to_lonlat(x, y, c_lon, c_lat)
            if point_in_ring((lon, lat), zone):
                obs_xy.append((x, y))
            x += step
        y += step

    # coverage cells at finer resolution
    cell = max(step / 3.0, 25.0)
    total = 0
    covered = 0
    gaps: list[list[float]] = []
    y = sy0
    while y <= sy1:
        x = sx0
        while x <= sx1:
            lon, lat = to_lonlat(x, y, c_lon, c_lat)
            if point_in_ring((lon, lat), zone):
                total += 1
                if any((x - ox) ** 2 + (y - oy) ** 2 <= radius_m ** 2 for ox, oy in obs_xy):
                    covered += 1
                else:
                    gaps.append([round(lon, 6), round(lat, 6)])
            x += cell
        y += cell

    obs_ll = []
    for ox, oy in obs_xy:
        lon, lat = to_lonlat(ox, oy, c_lon, c_lat)
        obs_ll.append([round(lon, 6), round(lat, 6)])
    ratio = round(covered / total, 3) if total else 0.0
    # cap gap list so payload stays small
    return {
        "observation_points": obs_ll,
        "coverage_ratio": ratio,
        "gaps": gaps[:200],
        "gap_count": len(gaps),
        "cells_total": total,
        "radius_m": radius_m,
        "spacing_m": spacing_m,
    }


def centroid(ring: list[list[float]]) -> list[float]:
    if not ring:
        return [0.0, 0.0]
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return [sum(xs) / len(xs), sum(ys) / len(ys)]
