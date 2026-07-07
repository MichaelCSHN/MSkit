# MSkit — Multi-Scenario Edge Intelligence Kit

MSkit 是面向民用/商用实景活动、演练、赛事、搜救和安保训练的 **黑 / 红 / 蓝三方智能规控平台**。黑方统揽全局，红方负责搜索检测，蓝方负责防护覆盖；系统通过 PNT、GOD/COD、CCD、路径规划、态势地图和报告导出形成闭环。

> **版本**：v1.3.2（2026年7月，三方叙事同步修订）｜**状态**：内部评审稿（Engineering Review Draft）｜**定位**：离线优先的三方实景智能规控平台

> ⚠️ 当前阶段优先目标是 **M0 MVP 立项演示 / 融资路演**。MVP 使用笔记本 + 无人机/素材导入验证黑方 PNT/规划、红方 GOD/COD、蓝方 CCD 的三方闭环；暂不采购或验证 Jetson、加固箱、LoRa、RTK、正式热成像模组、IP/EMC/认证和 Pilot Batch。

---

## 概述

MSkit 将无人机视频、图片、飞行日志、队伍轨迹、任务区域和事件标注统一到离线地图与 PNT 时间线中，服务于实景活动中的三类角色：

- **黑方**：组织者、裁判、调度方，负责活动配置、规则、边界、全局态势、路径规划、裁判/调度和报告归档。
- **红方**：攻方、搜救小队、巡检搜索小队，负责搜索、检测、识别、GOD/COD、发现点复核和证据提交。
- **蓝方**：守方、安保小队、防护/值守小队，负责 CCD、保护区、禁入区、覆盖缺口分析和巡查路径。

差异化定位：MSkit 的价值不是单点 AI 检测，而是 **黑方 PNT/规划 + 红方 GOD/COD + 蓝方 CCD** 的三方闭环；MVP 可用笔记本 + 无人机/素材导入先验证核心叙事，正式产品再升级到 Jetson、RTK、热成像、LoRa Mesh 和加固便携硬件。

## 核心应用场景

| 场景 | 三方结构 | 说明 | 优先级 |
|------|----------|------|--------|
| Hide and Seek 实景对抗赛 | 黑 / 红 / 蓝 | 黑方组织与裁判；红方搜索发现；蓝方隐藏、防护和覆盖设计 | P0 |
| 大型 Milsim 实景游戏 | 黑 / 红 / 蓝 | 黑方主办和安全裁判；红方搜索/推进；蓝方防护/守方；仅限民用模拟和赛事组织 | P0 |
| 安保训练 | 黑 / 红 / 蓝 | 黑方为教官/评估员；红方巡检发现异常；蓝方设计防护区和巡查路线 | P1 |
| 野外搜救 | 黑 / 红 | 黑方负责搜救调度和 PNT；红方执行搜索、GOD/COD 和证据提交；蓝方可选 | P0 |
| 灾害应急演练 | 黑 / 红 / 蓝 | 黑方组织演练；红方搜索受困点/风险点；蓝方维护安全区和物资区 | P1 |
| 越野定向 / 户外团队挑战赛 | 黑 / 红 / 蓝 | 黑方组织赛事；红方寻找检查点；蓝方维护安全区/补给点 | P2 |
| 大型营地 / 音乐节 / 户外活动安保 | 黑 / 蓝，可选红方 | 黑方主办；蓝方值守和巡查；红方可作为巡检搜索队 | P2 |
| 工业园区 / 农场 / 林地巡检 | 黑 / 红 / 蓝 | 黑方运营；红方巡检发现异常；蓝方维护边界和重点设施 | P2 |
| 生态观察与动物追踪 | 黑 / 红 | 黑方管理观察任务；红方采集动物/足迹/热源证据；遵守当地法规 | P3 |

## 黑 / 红 / 蓝三方架构

| 方别 | 角色 | 核心能力 | MVP 展示 |
|------|------|----------|----------|
| 黑方 | 活动、游戏、赛事、演练或任务的组织者 / 裁判 / 调度方 | 全局态势、规则、PNT、路径规划、裁判/调度、报告归档 | PNT 与全局规划 |
| 红方 | 游戏/竞赛攻方，或搜救小队、巡检搜索小队 | 检测、搜索、识别、发现点标注、证据采集 | GOD / COD |
| 蓝方 | 游戏/竞赛守方，或安保小队、防护/值守小队 | CCD、区域防护、覆盖设计、变化监测、巡查路径 | CCD 方案设计 |

> 三方架构只用于民用活动组织、模拟竞赛、搜救训练、安保巡检和户外团队协作；不得解释为军事指挥、武器化、打击排序或作战控制。

## 当前阶段优先文档（M0 MVP）

现阶段执行优先级如下：

1. **MVP PLAN**：`MSkit_v1.3.2_MVP_Development_Plan.md`
2. **MVP BOM**：`MSkit_v1.3.2_MVP_BOM_Cost_Table.md`
3. **MVP CHECKLIST**：`MSkit_v1.3.2_MVP_Development_Checklist.md`

正式工程版 `Development_Plan`、`BOM_Cost_Table`、`Development_Checklist` 保留为 **M1 之后的工程样机 / Pilot Batch / 量产路线参考**，不作为 M0 路演阶段的主执行文档。

## 产品变体一览

| 变体 | 计算模块 | AI 算力 | 热成像 | 基础 BOM | 目标零售价 | 估算毛利率 |
|------|----------|---------|--------|----------|-----------|-----------|
| Backpack Base | Orin Nano 8GB | 67 TOPS | 无 | $1,844 | $7,999 | ~77% |
| Backpack Thermal | Orin Nano 8GB | 67 TOPS | Boson 640 | $5,952 | $11,999 | ~50% |
| Team Base（原 Command Base） | Orin NX 16GB | 157 TOPS | 无 | $2,680 | $14,999 | ~82% |
| Team Thermal（原 Command Thermal） | Orin NX 16GB | 157 TOPS | Boson 640 | $6,788 | $17,999 | ~62% |
| Field Pro（原 Command Pro） | AGX Orin 32GB | 200 TOPS | Boson+ 640 | — | $24,999 | — |
| Field Max（原 Command Max） | AGX Orin 64GB | 275 TOPS | Boson+ 640 | — | $34,999 | — |

> BOM/毛利数据以 [正式 BOM 成本表](docs/MSkit_v1.3.2_BOM_Cost_Table.md) 为准；MVP 路演阶段以 [MVP BOM / 演示成本表](docs/MSkit_v1.3.2_MVP_BOM_Cost_Table.md) 为准。

## 关键指标

| 维度 | 指标 |
|------|------|
| AI 推理 | 模型推理：YOLOv8n INT8 ≥ 50 FPS（640×640, batch=1）；端到端视频：单路 1080p 输入 ≥25 FPS；MVP 阶段可用笔记本降级演示 |
| AI 精度 | 白天 mAP@0.5 ≥ 0.85（冻结测试集 ≥5,000 张）；夜间/热成像 ≥0.70（冻结测试集 ≥3,000 张）；MVP 不作为正式 mAP 验收 |
| 定位 | 正式版目标 RTK 水平 < 2cm，垂直 < 3cm；MVP 可用无人机日志或模拟轨迹，不承诺 RTK 精度 |
| 组网 | 正式版 LoRa Mesh 最多 8 节点；MVP 不做 LoRa 实物组网，用虚拟节点或日志模拟 |
| 续航 | 正式版 Backpack 24–48h / Team 12–24h+；MVP 不验证续航 |
| 环境 | 正式版 IP65/IP67 为整机装配后目标等级；MVP 不做环境/EMC/认证测试 |
| 软件栈 | MVP：笔记本 + FastAPI/React/SQLite/MapLibre；正式版：JetPack 6.2.1 + CUDA 12.6.10 + TensorRT 10.3 |
| 安全 | MVP 做基本导出和素材管理；正式版导出默认为加密包 + 二次确认 |
| MVP 演示 | 黑方 PNT/规划 + 红方 GOD/COD + 蓝方 CCD；硬件为笔记本 + 遥控器 + 无人机，或笔记本 + 无人机/离线素材；不做飞控控制 |
| 外协 | MVP 只允许短 Sprint 支持 D/E 能力；正式阶段对外按 6 个一级包 A–F 管理 |

## 文档索引

| 文档 | 说明 |
|------|------|
| [MSkit_v1.3.2_MVP_Development_Plan.md](docs/MSkit_v1.3.2_MVP_Development_Plan.md) | **MVP PLAN（现阶段优先）**：6 周 M0 路演开发计划，聚焦 Hide and Seek 主脚本、野外搜救备选脚本、黑方 PNT、红方 GOD/COD、蓝方 CCD |
| [MSkit_v1.3.2_MVP_BOM_Cost_Table.md](docs/MSkit_v1.3.2_MVP_BOM_Cost_Table.md) | **MVP BOM（现阶段优先）**：笔记本、无人机、素材、短期外协和路演成本；不混入正式产品 BOM |
| [MSkit_v1.3.2_MVP_Development_Checklist.md](docs/MSkit_v1.3.2_MVP_Development_Checklist.md) | **MVP CHECKLIST（现阶段优先）**：W1–W6 执行检查、路演当天检查、转正式工程条件 |
| [MSkit_v1.3.2_Spec.md](docs/MSkit_v1.3.2_Spec.md) | **v1.3.2 主规格（变更集/覆盖层）**：承载最新口径、命名、数值、合规表述、三方架构、MVP 边界和外协一级包执行口径；工程明细仍见 v1.3 明细规格 |
| [MSkit_v1.3.2_Positioning_and_Scenarios.md](docs/MSkit_v1.3.2_Positioning_and_Scenarios.md) | **三方叙事定位与应用场景**：重构项目定位、目标、核心/扩展场景和 MVP 场景优先级 |
| [MSkit_v1.3.2_Tri_Party_Functions.md](docs/MSkit_v1.3.2_Tri_Party_Functions.md) | **黑/红/蓝三方架构与功能矩阵**：明确黑方、红方、蓝方的通用功能、专有功能、权限边界和 MVP 展示取舍 |
| [MSkit_v1.3.2_MVP_Demo_Plan.md](docs/MSkit_v1.3.2_MVP_Demo_Plan.md) | **MVP 演示方案**：用于立项/融资路演，展示黑方 PNT/规划、红方 GOD/COD、蓝方 CCD 的三方闭环 |
| [MSkit_v1.3.2_Development_Plan.md](docs/MSkit_v1.3.2_Development_Plan.md) | **正式工程 PLAN（M1 后）**：18 个月工程样机、认证、Pilot Batch 和 GA 路线 |
| [MSkit_v1.3.2_BOM_Cost_Table.md](docs/MSkit_v1.3.2_BOM_Cost_Table.md) | **正式工程 BOM（M1 后）**：Jetson、加固箱、RTK、LoRa、热成像、电池、Pilot Batch 经济性 |
| [MSkit_v1.3.2_Development_Checklist.md](docs/MSkit_v1.3.2_Development_Checklist.md) | **正式工程 CHECKLIST（M1 后）**：工程样机、认证、无人机数据接入、授权、外协一级包治理项 |
| [MSkit_v1.3.2_Outsourcing_Modules.md](docs/MSkit_v1.3.2_Outsourcing_Modules.md) | **v1.3.2 外协分包方案**：6 个一级外包包 + 1 个内部核心包；MVP 仅允许 D/E 能力小范围短期支持 |
| [v1.3 明细规格](docs/MSkit_v1.3_Spec.md) | **明细基线（仍然有效）**：完整硬件/接口/附录 A–E/术语表/SBOM 许可证/风险矩阵；v1.3.2 未覆盖的明细以此为准 |
| [v1.3 明细开发计划](docs/MSkit_v1.3_Development_Plan.md) | **明细基线（仍然有效）**：完整 WP 表（WP-ID / DoD / 关口）；v1.3.2 计划为其变更集 |
| [v1.3 明细 BOM 表](docs/MSkit_v1.3_BOM_Cost_Table.md) | **明细基线（仍然有效）**：元件级成本明细；v1.3.2 BOM 表为其同步/覆盖层 |
| [v1.3 明细 Checklist](docs/MSkit_v1.3_Development_Checklist.md) | **明细基线（仍然有效）**：逐项检查清单；v1.3.2 Checklist 覆盖不一致项 |

> **规格来源约定（分层权威）**：M0 阶段以 MVP PLAN / MVP BOM / MVP CHECKLIST 为执行主文档；M1 之后以正式工程 PLAN / BOM / CHECKLIST 为工程主文档。v1.3.2 文档集是 v1.3 的**变更集/覆盖层**，二者配套使用。

### 尚未提供的附属图（规格中被引用）

以下文件在历史规格中被引用，但当前仓库尚未提供；未入库前不得作为规格完整性交付项：

- `MSkit_v1.3_Gantt_Chart.png` — 18 个月开发计划甘特图
- `MSkit_v1.3_BOM_Analysis.png` — BOM 成本结构分析图
- `MSkit_v1.3_Competitive_Analysis.png` — 竞品对标分析图

## 实施计划

| 阶段 | 时间 | 主文档 | 交付物 |
|------|------|--------|--------|
| M0 MVP 路演演示 | 6 周 | MVP PLAN / MVP BOM / MVP CHECKLIST | 三方笔记本版 MVP：黑方 PNT/规划、红方 GOD/COD、蓝方 CCD、报告导出、演示脚本、录屏备份 |
| M1 Spec 冻结 | M2 末 | 正式工程 PLAN / BOM / CHECKLIST | v1.3.2 签署版 + 架构设计 + 一级外包包 SOW 草案 |
| M2 POC 验证 | M4.5 末 | 正式工程 PLAN | 可运行原型（Jetson + 传感器联调） |
| M3 Alpha 软件 | M8 末 | 正式工程 PLAN | 全部功能模块初版 |
| M4 Beta 硬件定型 | M11 末 | 正式工程 PLAN / BOM | EVT2 样机 |
| M5 认证通过 | M13.5 末 | 正式工程 CHECKLIST | SRRC + CE/FCC + UN38.3 证书/报告 |
| M6 首批交付 | M15 末 | 正式工程 PLAN / BOM / CHECKLIST | 50 套 Pilot Batch + 完整文档包 |
| M7 Pilot 反馈 | M16 末 | 正式工程 PLAN | 试点问题清单 + 固件/结构修订 |
| M8 PVT 小批量 | M17 末 | 正式工程 PLAN / BOM / CHECKLIST | PVT 样机 + 良率报告 + 售后流程 |
| M9 GA 发布 | M18 末 | 正式工程文档集 | v1.4 量产规格 + 销售/认证包 |

MVP 推荐预算档位：**标准路演版 $25,000–$60,000**。正式工程研发预算仍按团队地区分三档：极简创始 **$400k–$500k** / 中国工程团队 **$600k–$900k** / 美欧日团队 **$1.2M–$2.0M**。

## 合规

严格遵循民用法规，避免军用采购、武器化与作战用途表述。MVP 路演阶段不做无人机飞控控制、不下发飞行指令、不展示军事化目标分类、武器识别、打击排序或作战控制能力。正式工程阶段再覆盖 SRRC/FCC/CE 无线电认证、RoHS/REACH/WEEE 环保、《个人信息保护法》/GDPR 数据保护、UN38.3 锂电池运输、EN 62368-1 产品安全和完整 SBOM。

---

> 文档受版本控制管理，所有变更需经 CCB（变更控制委员会）审批。详见 [v1.3.2 规格文档](docs/MSkit_v1.3.2_Spec.md)。
