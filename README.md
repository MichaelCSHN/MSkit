# MSkit — Multi-Scenario Edge Intelligence Kit

便携式、加固的**边缘智能信息规控系统**，服务于纯民用与商用场景（Milsim 模拟、野外生态观察与合法追踪、作业安保巡检、救援演练、户外探险团队协调）。

> **版本**：v1.3.2（2026年7月，文档同步修订）｜**状态**：内部评审稿（Engineering Review Draft）｜**定位**：离线优先的多源感知 + AI 辅助决策 + 活动/任务管理

> ⚠️ 当前文档为**内部评审稿**，非正式对外规格。价格、性能与合规项待供应商 RFQ、样品验证、法律审查与认证预测试后方可冻结。变体毛利率**仅按硬件 BOM 口径**，首批 50 套为 Pilot Batch，不承担全部研发摊销（详见[规格 §9](docs/MSkit_v1.3.2_Spec.md)）。

---

## 概述

MSkit 在一台加固便携箱内集成高算力边缘 AI、厘米级 RTK 定位、可见光/热成像、LoRa Mesh 组网与完整的任务/告警/报告软件栈，可在无网络环境下独立工作。核心设计原则：**合规优先、安全默认、实用导向、可扩展、成本可控、可维护**。

差异化定位：同时具备高算力边缘 AI（67–275 TOPS）+ 厘米级 RTK + 热成像 + LoRa Mesh + 加固便携的民用/商用级边缘智能产品。

## 产品变体一览

| 变体 | 计算模块 | AI 算力 | 热成像 | 基础 BOM | 目标零售价 | 估算毛利率 |
|------|----------|---------|--------|----------|-----------|-----------|
| Backpack Base | Orin Nano 8GB | 67 TOPS | 无 | $1,844 | $7,999 | ~77% |
| Backpack Thermal | Orin Nano 8GB | 67 TOPS | Boson 640 | $5,952 | $11,999 | ~50% |
| Team Base（原 Command Base） | Orin NX 16GB | 157 TOPS | 无 | $2,680 | $14,999 | ~82% |
| Team Thermal（原 Command Thermal） | Orin NX 16GB | 157 TOPS | Boson 640 | $6,788 | $17,999 | ~62% |
| Field Pro（原 Command Pro） | AGX Orin 32GB | 200 TOPS | Boson+ 640 | — | $24,999 | — |
| Field Max（原 Command Max） | AGX Orin 64GB | 275 TOPS | Boson+ 640 | — | $34,999 | — |

> BOM/毛利数据以 [BOM 成本表](docs/MSkit_v1.3.2_BOM_Cost_Table.md) 为准；历史表仍保留在 `docs/MSkit_v1.3_BOM_Cost_Table.md`。

## 关键指标

| 维度 | 指标 |
|------|------|
| AI 推理 | 模型推理：YOLOv8n INT8 ≥ 50 FPS（640×640, batch=1）；端到端视频：单路 1080p 输入 ≥25 FPS |
| AI 精度 | 白天 mAP@0.5 ≥ 0.85（冻结测试集 ≥5,000 张）；夜间/热成像 ≥0.70（冻结测试集 ≥3,000 张） |
| 定位 | RTK 水平 < 2cm，垂直 < 3cm（u-blox ZED-F9P） |
| 组网 | LoRa Mesh 最多 8 节点，AES-256-GCM；仅承载低速遥测，文件传输走 Wi-Fi/USB/以太网 |
| 续航 | Backpack 24–48h / Team 12–24h+（受控热插拔双电池） |
| 环境 | IP65（可选 IP67）为整机装配后目标等级；MIL-STD-810H 为设计验证方法，第三方测试前不宣称 certified |
| 软件栈 | JetPack 6.2.1 + CUDA 12.6.10 + TensorRT 10.3，Docker + systemd |
| 安全 | LUKS2 全盘加密 + TPM 2.0 + Secure Boot + RBAC + 审计日志；导出默认为加密包 + 二次确认 |

## 文档索引

| 文档 | 说明 |
|------|------|
| [MSkit_v1.3.2_Spec.md](docs/MSkit_v1.3.2_Spec.md) | **v1.3.2 主规格文档**：当前权威规格，覆盖需求、硬件、软件、接口、测试、预算、风险、验收 |
| [MSkit_v1.3.2_Development_Plan.md](docs/MSkit_v1.3.2_Development_Plan.md) | **v1.3.2 同步开发计划**：统一 AI 测量口径、无人机数据接入边界、Class A/B、加密导出验收、M16–M18 |
| [MSkit_v1.3.2_BOM_Cost_Table.md](docs/MSkit_v1.3.2_BOM_Cost_Table.md) | **v1.3.2 BOM 同步表**：地区化通信 SKU、电池化学体系分层、Pilot Batch 经济性 |
| [MSkit_v1.3.2_Development_Checklist.md](docs/MSkit_v1.3.2_Development_Checklist.md) | **v1.3.2 同步 Checklist**：修正 LoRa、EMC、环境测试、无人机、加密导出与授权检查项 |
| [历史 v1.3 规格](docs/MSkit_v1.3_Spec.md) | 历史基线，保留用于 diff，不作为 v1.3.2 权威执行口径 |
| [历史 v1.3 开发计划](docs/MSkit_v1.3_Development_Plan.md) | 历史基线，保留用于 diff |
| [历史 v1.3 BOM 表](docs/MSkit_v1.3_BOM_Cost_Table.md) | 历史基线，保留用于 diff |
| [历史 v1.3 Checklist](docs/MSkit_v1.3_Development_Checklist.md) | 历史基线，保留用于 diff |

> **规格来源约定**：`MSkit_v1.3.2_Spec.md` 为当前权威源；历史 v1.3 文档保留用于 diff。如需 Word/PDF 版本用于对外分发，从当前权威 Markdown 导出。

### 尚未提供的附属图（规格中被引用）

以下文件在历史规格中被引用，但当前仓库尚未提供；未入库前不得作为规格完整性交付项：

- `MSkit_v1.3_Gantt_Chart.png` — 18 个月开发计划甘特图
- `MSkit_v1.3_BOM_Analysis.png` — BOM 成本结构分析图
- `MSkit_v1.3_Competitive_Analysis.png` — 竞品对标分析图

## 实施计划（18 个月里程碑）

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| M1 Spec 冻结 | M2 末 | v1.3.2 签署版 + 架构设计 |
| M2 POC 验证 | M4.5 末 | 可运行原型（Jetson + 传感器联调） |
| M3 Alpha 软件 | M8 末 | 全部功能模块初版 |
| M4 Beta 硬件定型 | M11 末 | EVT2 样机 |
| M5 认证通过 | M13.5 末 | SRRC + CE/FCC + UN38.3 证书/报告 |
| M6 首批交付 | M15 末 | 50 套 Pilot Batch + 完整文档包 |
| M7 Pilot 反馈 | M16 末 | 试点问题清单 + 固件/结构修订 |
| M8 PVT 小批量 | M17 末 | PVT 样机 + 良率报告 + 售后流程 |
| M9 GA 发布 | M18 末 | v1.4 量产规格 + 销售/认证包 |

研发预算按团队地区分三档：极简创始 **$400k–$500k** / 中国工程团队 **$600k–$900k** / 美欧日团队 **$1.2M–$2.0M**（含软件授权与数据集，另留 15% 应急金）。

## 合规

严格遵循民用法规，避免军用采购、武器化与作战用途表述。覆盖 SRRC/FCC/CE 无线电认证、RoHS/REACH/WEEE 环保、《个人信息保护法》/GDPR 数据保护、UN38.3 锂电池运输、EN 62368-1 产品安全，并提供完整 SBOM（SPDX 格式）。环境与 EMC 指标均为设计目标，必须经目标市场和 SKU 对应测试后方可对外宣称。

---

> 文档受版本控制管理，所有变更需经 CCB（变更控制委员会）审批。详见 [v1.3.2 规格文档](docs/MSkit_v1.3.2_Spec.md)。
