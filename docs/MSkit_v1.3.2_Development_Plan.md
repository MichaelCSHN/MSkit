# MSkit v1.3.2 开发计划同步版

> **基线**：`MSkit_v1.3.2_Spec.md`｜**状态**：内部评审稿｜**目的**：同步主规格中的 AI 测试口径、无人机数据接入边界、EMC Class A/B、环境测试声明、加密导出、BOM 地区化要求和外协一级包结构。

---

## 1. 统一度量口径

| 指标 | v1.3.2 统一测量条件 | 验收说明 |
|------|--------------------|----------|
| 模型推理 FPS | 640×640, batch=1, INT8, TensorRT/DeepStream, nvpmodel 最高档，稳态 5 分钟均值 | YOLOv8n ≥50 FPS |
| 端到端视频 FPS | 1080p 输入，含解码、resize、推理、跟踪、叠加、WebSocket 输出 | 单路 ≥25 FPS，同时报告端到端延迟；内部 Integration Owner 牵头 C/D/E 联合验收 |
| mAP | mAP@0.5，自建冻结验证集；白天 ≥5,000 张，夜间/热成像 ≥3,000 张 | 同时报告 Precision / Recall / F1 / 误报率 / 漏报率 |
| RTK 精度 | 静态观测 1 小时，相对已知基准点的水平/垂直 StdDev | 水平 <2cm，垂直 <3cm；归入 C 包/OP-12 |
| 续航 | 标准负载循环，放电至 BMS 保护截止 | Backpack >24h，Team >12h |
| 环境测试 | 参考 MIL-STD-810H 514.8/516.8 与 IEC 60068 方法 | 第三方报告前不得宣称 certified |
| EMC | 消费/户外 SKU 目标 Class B；工业/商用 SKU 可按 Class A | 按目标市场与 SKU 测试 |

---

## 2. 外协一级包与开发计划映射

| 一级包 | 包含 OP | 开发阶段 | 内部 Owner | 关键验收 |
|--------|---------|----------|------------|----------|
| A. Rugged Hardware & Mechatronics | OP-01 + OP-02 + OP-03 | M1–M11 | HW / ME | 结构、电源、热设计、受控热插拔、环境预验证 |
| B. RF / Wireless / Certification | OP-04 + OP-11 中认证技术部分 | M1–M13.5 | HW / SCM / LEG | 地区化 SKU、RF/EMC 预扫描、认证资料 |
| C. Edge Platform & Device Firmware | OP-05 + OP-09 + OP-12 | M2–M8 | EMB Lead | Jetson 镜像、OTA、LoRa、RTK/GNSS/IMU 融合 |
| D. Application Software | OP-07 + OP-08 | M3–M9 | FS Lead | 地图、任务、报告、Dashboard、视频 UI 链路 |
| E. AI Data & Model Optimization | OP-06 | M2–M10 | AI Lead | 数据集、mAP、模型 FPS、TensorRT engine |
| F. Manufacturing & Test Fixtures | OP-10 | M8–M15 | QA / SCM | 试产 SOP、工装、出厂测试、良率报告 |
| 内部核心包 | 架构/安全/接口/验收/合规边界 | M1–M18 | PM / Architect / QA | 接口冻结、安全策略、最终整机签署 |

> 对外 SOW / RFP 使用一级包 A–F；OP-01–OP-12 只作为二级 WBS、验收点和内部跟踪项。未经 CCB 批准，不单独把 OP 拆成独立合同。

---

## 3. 关键 Go/No-Go 关口

| 关口 | 月份 | Go 判据 |
|------|------|---------|
| G1 Spec 冻结 | M2 | v1.3.2 规格、BOM、Checklist、开发计划、外协一级包 SOW 口径一致；无 P0 文档冲突 |
| G2 POC 技术解风险 | M4.5 | AI 模型推理、端到端视频链路、RTK、热成像取流、LoRa 低速遥测、电池安全台架实测达标 |
| G3 Alpha 软件 | M8 | Lite/Standard/Pro 分层部署跑通；无人机仅做日志、媒体、视频数据接入；C/D/E 包接口联调通过 |
| G4 Beta 硬件定型 | M11 | A 包结构/电源/热设计收敛；B 包 IP/环境/EMC 预测试按目标 SKU 完成；电池运输路径确认 |
| G5 认证通过 | M13.5 | SRRC/CE/FCC/UN38.3/RoHS/REACH 等文档齐备 |
| G6 首批交付 | M15 | F 包支持 50 套 Pilot Batch，出厂测试 100% 通过 |
| G7 Pilot 反馈闭环 | M16 | P0/P1 缺陷闭环，现场故障率 <5% |
| G8 PVT 小批量 | M17 | 良率达标，SOP、售后、备件流程冻结 |
| G9 GA 发布 | M18 | v1.4 量产规格和销售/认证包完成 |

---

## 4. 必须同步的工作包修订

| WP | 修订内容 | Owner | 关联一级包 |
|----|----------|-------|------------|
| WP-1.1 | 法务评审术语：避免军用采购、武器化与作战用途表述；不再写“杜绝任何军事化表述”这种无法完全匹配 Milsim 场景的绝对表述 | PM/LEG | 内部核心包 |
| WP-1.3 | KPI 拆分模型推理 FPS 与端到端视频 FPS；端到端 FPS 由内部 Integration Owner 签署 | PM/AI/EMB/QA | C/D/E + 内部 |
| WP-2.6 | LoRa 按地区化 SKU 采购与测试；只验收低速遥测，不验收文件传输 | EMB/SCM | C + B |
| WP-2.7 | 标准版优先 Li-ion/LiFePO4；LiPo 仅用于工程样机/专业用户版本；>300Wh 按危险品运输评估 | HW/SCM/LEG | A + B |
| WP-2.9 | RTK/GNSS + IMU 定位融合、多摄像头同步触发归入 C 包/OP-12 | EMB/QA | C |
| WP-3.3 | YOLOv8/Ultralytics 商用授权必须在 v1.4 前落定；否则替换宽松许可框架并重测性能 | AI/LEG | E + 内部 LEG |
| WP-3.7.2 | 加密导出为加密包导出 + PIN/FIDO2/本地账户二次确认；不得默认输出明文 | EMB/FS | 内部安全 + C/D |
| WP-4.3.1 | 环境测试为设计验证；第三方报告前不得宣称 MIL-STD-810H certified | HW/QA | A |
| WP-4.4.1 | EMC 按消费 Class B / 工业 Class A 目标拆分 | HW/QA | B |
| WP-4.6（新增） | 无人机集成仅做日志、媒体和视频流接入；控制类集成不纳入 MVP，需另行合规与安全评审 | EMB/PM | C/D + 内部 LEG |

---

## 5. v1.3.2 不纳入 MVP 的事项

- 控制类无人机集成。
- LoRa 文件传输。
- 明文一键导出。
- 未经授权的闭源 YOLOv8 商用嵌入。
- 未经第三方测试的 MIL-STD-810H certified 宣称。
- 未经目标市场确认的“868/915MHz 通用”无线配置。
- 未经 CCB 批准把 OP-01–OP-12 拆成独立外协合同。
