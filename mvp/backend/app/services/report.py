"""Generate a demo report (Markdown + minimal HTML) for an activity.

Includes an explicit real-vs-simulated disclosure block, per
docs/MSkit_v1.3.2_MVP_Demo_Plan.md §10.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone


def build_markdown(activity, zones, tracks, detections) -> str:
    real = [d for d in detections if not d.simulated]
    sim = [d for d in detections if d.simulated]
    confirmed = [d for d in detections if d.status == "confirmed"]
    lines = []
    lines.append(f"# 活动报告：{activity.name}")
    lines.append("")
    lines.append(f"- 场景：{activity.scenario}")
    lines.append(f"- 中心：{activity.center_lat:.5f}, {activity.center_lon:.5f}")
    lines.append(f"- 生成时间（UTC）：{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S}")
    lines.append("")
    lines.append("## 组织方 · 全局概览")
    lines.append(f"- 区域数：{len(zones)}（含禁入/安全/搜索/防护）")
    lines.append(f"- 轨迹数：{len(tracks)}")
    lines.append(f"- 发现点：{len(detections)}（确认 {len(confirmed)}）")
    lines.append("")
    lines.append("## 搜索方 · 发现")
    if detections:
        lines.append("| 类别 | 置信度 | 位置 | 状态 | 来源 |")
        lines.append("|------|--------|------|------|------|")
        for d in detections:
            src = "模拟/预置" if d.simulated else "真实推理"
            lines.append(f"| {d.label} | {d.confidence:.2f} | {d.lat:.5f},{d.lon:.5f} "
                         f"| {d.status} | {src} |")
    else:
        lines.append("（无发现点）")
    lines.append("")
    lines.append("## 防护方 · 覆盖")
    prot = [z for z in zones if z.kind == "protection"]
    lines.append(f"- 防护区数：{len(prot)}")
    lines.append("")
    lines.append("## 真实 vs 模拟披露")
    lines.append(f"- 真实模型推理发现：{len(real)}")
    lines.append(f"- 模拟/预置发现：{len(sim)}")
    lines.append("- 说明：MVP 阶段轨迹可能为飞行日志或模拟轨迹，覆盖/变化为简化算法，"
                 "不承诺 RTK 实测精度；正式性能口径见工程规格。")
    lines.append("")
    return "\n".join(lines)


def build_html(markdown_text: str, title: str) -> str:
    # Minimal, dependency-free markdown-ish rendering (headings, tables, lists).
    body_lines = []
    in_table = False
    for raw in markdown_text.splitlines():
        line = raw.rstrip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue  # separator row
            if not in_table:
                body_lines.append("<table>")
                in_table = True
            tag = "td"
            body_lines.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            body_lines.append("</table>")
            in_table = False
        if line.startswith("# "):
            body_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            body_lines.append(f"<li>{html.escape(line[2:])}</li>")
        elif line == "":
            body_lines.append("")
        else:
            body_lines.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        body_lines.append("</table>")
    style = (
        "body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:820px;"
        "margin:2rem auto;padding:0 1rem;color:#1a1a1a}"
        "table{border-collapse:collapse;width:100%;margin:1rem 0}"
        "td{border:1px solid #ccc;padding:4px 8px;font-size:14px}"
        "h1{border-bottom:2px solid #333}h2{margin-top:1.5rem;color:#333}"
        "li{margin:2px 0}"
    )
    return (f"<!doctype html><html lang=zh><head><meta charset=utf-8>"
            f"<title>{html.escape(title)}</title><style>{style}</style></head>"
            f"<body>{''.join(body_lines)}</body></html>")
