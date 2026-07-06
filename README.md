# MSkit — Multi-Scenario Edge Intelligence Kit

便携式、加固的**边缘智能信息规控系统**，服务于纯民用与商用场景（Milsim 模拟、野外追踪、作业安保巡检、救援演练、户外探险团队协调）。

> **版本**：v1.3（2026年7月）｜**状态**：正式发布｜**定位**：离线优先的多源感知 + AI 辅助决策 + 任务管理

---

## 概述

MSkit 在一台 Pelican 加固箱内集成高算力边缘 AI、厘米级 RTK 定位、可见光/热成像、LoRa Mesh 组网与完整的任务/告警/报告软件栈，可在无网络环境下独立工作。核心设计原则：**合规优先、安全默认、实用导向、可扩展、成本可控、可维护**。

差异化定位：唯一同时具备高算力边缘 AI（67–275 TOPS）+ 厘米级 RTK + 热成像 + LoRa Mesh + 加固便携的民用级产品。

## 产品变体一览

| 变体 | 计算模块 | AI 算力 | 热成像 | 基础 BOM | 目标零售价 | 估算毛利率 |
|------|----------|---------|--------|----------|-----------|-----------|
| Backpack Base | Orin Nano 8GB | 67 TOPS | 无 | $1,844 | $7,999 | ~77% |
| Backpack Thermal | Orin Nano 8GB | 67 TOPS | Boson 640 | $5,952 | $11,999 | ~50% |
| Command Base | Orin NX 16GB | 157 TOPS | 无 | $2,680 | $14,999 | ~82% |
| Command Thermal | Orin NX 16GB | 157 TOPS | Boson 640 | $6,788 | $17,999 | ~62% |
| Command Pro | AGX Orin 32GB | 200 TOPS | Boson+ 640 | — | $24,999 | — |
| Command Max | AGX Orin 64GB | 275 TOPS | Boson+ 640 | — | $34,999 | — |

> BOM/毛利数据以 [BOM 成本表](docs/MSkit_v1.3_BOM_Cost_Table.md) 为准。

## 关键指标

| 维度 | 指标 |
|------|------|
| AI 推理 | YOLOv8n INT8 > 50 FPS（白天 mAP > 92%，夜间 > 75%） |
| 定位 | RTK 水平 < 2cm，垂直 < 3cm（u-blox ZED-F9P） |
| 组网 | LoRa Mesh，最多 8 节点，AES-256-GCM 加密 |
| 续航 | Backpack 24–48h / Command 12–24h+（热插拔双电池） |
| 环境 | IP65（可选 IP67），-20°C ~ +55°C，MIL-STD-810H |
| 软件栈 | JetPack 6.2.1 + CUDA 12.2 + TensorRT 10.3，Docker + systemd |
| 安全 | LUKS2 全盘加密 + TPM 2.0 + Secure Boot + RBAC + 审计日志 |

## 文档索引

| 文档 | 说明 |
|------|------|
| [MSkit_v1.3_Spec.md](docs/MSkit_v1.3_Spec.md) | **主规格文档**（版本可控 Markdown）：需求、硬件、软件、接口、测试、预算、风险、验收、附录 |
| [MSkit_Spec_v1.3.docx](docs/MSkit_Spec_v1.3.docx) | 主规格文档的 Word 版本（用于对外分发/评审签署） |
| [MSkit_v1.3_BOM_Cost_Table.md](docs/MSkit_v1.3_BOM_Cost_Table.md) | 详细 BOM 成本分解表（50 套小批量）、变体总览、研发预算 |
| [MSkit_v1.3_Development_Checklist.md](docs/MSkit_v1.3_Development_Checklist.md) | 按 Phase/模块细分的 18 个月开发检查清单 + 性能验收清单 |

> **规格来源约定**：`MSkit_v1.3_Spec.md`（Markdown）与 `MSkit_Spec_v1.3.docx`（Word）内容应保持同步；如有冲突，以 Markdown 版本为准（便于 diff 与评审）。

### 尚未提供的附属图（规格中被引用）

以下文件在规格中被引用，但当前仓库尚未提供，待补充：

- `MSkit_v1.3_Gantt_Chart.png` — 18 个月开发计划甘特图
- `MSkit_v1.3_BOM_Analysis.png` — BOM 成本结构分析图
- `MSkit_v1.3_Competitive_Analysis.png` — 竞品对标分析图

## 实施计划（18 个月里程碑）

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| M1 Spec 冻结 | M2 末 | v1.3 签署版 + 架构设计 |
| M2 POC 验证 | M4.5 末 | 可运行原型（Jetson + 传感器联调） |
| M3 Alpha 软件 | M8 末 | 全部功能模块初版 |
| M4 Beta 硬件定型 | M11 末 | EVT2 样机 |
| M5 认证通过 | M13.5 末 | SRRC + CE/FCC 证书 |
| M6 首批交付 | M15 末 | 50 套量产机 + 完整文档包 |

研发预算约 **$400,000**（18 个月冷启动团队），建议预留 15% 应急金。

## 合规

严格遵循民用法规，杜绝军事化表述或功能。覆盖 SRRC/FCC/CE 无线电认证、RoHS/REACH/WEEE 环保、《个人信息保护法》/GDPR 数据保护、UN38.3 锂电池运输、EN 62368-1 产品安全，并提供完整 SBOM（SPDX 格式）。

---

> 文档受版本控制管理，所有变更需经 CCB（变更控制委员会）审批。详见 [规格文档](docs/MSkit_v1.3_Spec.md)。
