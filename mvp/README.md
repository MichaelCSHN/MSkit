# MSkit MVP — 三方实景智能规控（笔记本演示版）

M0 路演 MVP：用**笔记本 + 无人机/离线素材**演示 **组织方 / 搜索方 / 防护方** 三方闭环——
组织方 定位态势/规划、搜索方 目标检测/变化检测、防护方 覆盖规划、报告导出。

> 对应文档：[MVP 开发计划](../docs/MSkit_v1.3.2_MVP_Development_Plan.md) ·
> [MVP 演示方案](../docs/MSkit_v1.3.2_MVP_Demo_Plan.md) ·
> [三方架构（权威）](../docs/MSkit_v1.3.2_Tri_Party_Functions.md)
>
> ⚠️ **真实 vs 模拟**：MVP 中轨迹可为飞行日志或**模拟轨迹**，发现点可为**预置/模拟**（`simulated=true`），
> 覆盖/变化为简化算法，**不承诺 RTK <2cm 实测精度**。路演须如实标注（见 MVP_Demo_Plan §10）。

## 结构

```
mvp/
  backend/   FastAPI + SQLite：数据接入、检测、覆盖规划(CCD)、路径规划(A*)、报告
  frontend/  Vite + React + MapLibre GL：三方地图态势、角色切换、图层
  data/sample/  样例上传数据（GPX/CSV）
```

## 后端（FastAPI）

```bash
cd mvp/backend
python -m venv .venv
.venv/Scripts/activate            # Windows；macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- 首次启动自动建库并**播种一个 Hide-and-Seek 演示活动**（区域 + 搜索航迹 + 模拟发现点）。
- 交互式 API 文档：<http://localhost:8000/docs>
- 健康检查：`GET /api/health` → `{"status":"ok","yolo_available":false}`

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/activities` | 活动列表 |
| GET | `/api/activities/{id}/state?role=organizer\|search\|protection` | 地图聚合态势（GeoJSON，按角色过滤） |
| POST | `/api/activities/{id}/tracks` | 上传 GPX/CSV 航迹（multipart：`file`,`team`,`name`） |
| POST | `/api/activities/{id}/detections/simulate` | 沿航迹生成模拟发现点 `{track_id,count}` |
| POST | `/api/detections/{id}/review` | 复核 `{status:confirmed\|rejected,note}` |
| POST | `/api/activities/{id}/coverage` | 防护方覆盖规划 `{zone_id,radius_m,spacing_m}` → 观测点/覆盖率/盲区 |
| POST | `/api/activities/{id}/route` | 组织/搜索路径规划 `{start:[lon,lat],goal:[lon,lat]}`（A* 绕禁入区） |
| GET | `/api/activities/{id}/report.html` `report.md` | 演示报告（含真实 vs 模拟披露） |

真实目标检测（可选）：安装 `ultralytics`（AGPL-3.0，商用需授权决策）后，`detect_image` 走 YOLOv8n；
未安装则自动回落到模拟发现点。

## 前端（Vite + React + MapLibre）

```bash
cd mvp/frontend
npm install
npm run dev            # http://localhost:5173
```

前端默认连后端 `http://localhost:8000`。地图底图开发期用在线 OSM 栅格；
离线 MBTiles/OSM 瓦片为后续项（正式离线演示前替换）。

## 6 周计划与验收

以 [MVP_Development_Plan §5–§7](../docs/MSkit_v1.3.2_MVP_Development_Plan.md) 为准，本目录只承载实现。
