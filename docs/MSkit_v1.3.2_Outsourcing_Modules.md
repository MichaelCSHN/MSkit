# MSkit v1.3.2 外协分包方案（一级包 + OP 工作包映射）

> **基线**：`MSkit_v1.3.2_Spec.md` + v1.3 明细文档  
> **状态**：内部评审稿 / 外协规划建议  
> **目的**：将原 OP-01–OP-12 工作分解升级为更适合发包管理的“6 个一级外包包 + 1 个内部核心包”结构，同时保留 OP 作为二级 WBS、验收项和接口治理单元。

---

## 1. 总体结论

MSkit 可以并行外协开发，但不应把 OP-01–OP-12 直接拆成 12 个独立合同。OP 层级适合作为内部 WBS 与验收颗粒度；对外发包应按同类能力和耦合关系合并为 6 个一级包。

推荐执行结构：

- **内部核心包（不外包）**：系统架构、接口冻结、合规边界、安全架构、数据模型、供应商协调、最终集成与验收。
- **A. Rugged Hardware & Mechatronics**：结构、电源、电池、热设计、环境预验证。
- **B. RF / Wireless / Certification**：地区化无线 SKU、天线、射频预扫描、认证路径。
- **C. Edge Platform & Device Firmware**：Jetson BSP、系统镜像、OTA、LoRa 低速遥测、RTK/GNSS/IMU 融合。
- **D. Application Software**：地图、导航、任务、报告、Dashboard、端到端视频 UI 链路。
- **E. AI Data & Model Optimization**：数据集、标注、训练、量化、TensorRT/DeepStream 模型层优化。
- **F. Manufacturing & Test Fixtures**：试产、工装、出厂测试、良率、FRU/售后流程。

> **发包规则**：对外 SOW / RFP 使用一级包 A–F；OP-01–OP-12 只作为二级工作包、验收项、内部跟踪项。未经 CCB 批准，不单独把 OP 拆成独立合同。

---

## 2. 内部核心包（不外包）

| 内部保留事项 | 原因 | 内部 Owner |
|--------------|------|------------|
| 产品需求与合规边界 | 涉及民用定位、禁用功能、宣传口径、法律责任 | PM / LEG |
| 系统架构与接口冻结 | 所有外包包依赖统一接口；接口失控会导致集成失败 | System Architect |
| 安全架构 | LUKS、TPM、Secure Boot、RBAC、审计、加密导出涉及核心信任边界 | EMB Lead / FS Lead |
| 数据模型与 API 契约 | 前端、AI、地图、报告、Mesh、定位融合都依赖统一 schema | FS Lead |
| 端到端集成 Owner | 供应商只能证明模块达标，整机指标必须内部签署 | QA / Integration |
| 供应商选择与合规判断 | 热成像、无线、电池、开源许可证、隐私均涉及公司责任 | SCM / LEG |
| 控制类无人机集成 | v1.3.2 不纳入 MVP；如未来开展，需单独安全与合规评审 | PM / LEG / EMB |

---

## 3. 一级外包包与 OP 映射

| 一级包 | 合并 OP | 主要交付 | 内部 Owner | 是否首批启动 |
|--------|---------|----------|------------|--------------|
| A. Rugged Hardware & Mechatronics | OP-01 + OP-02 + OP-03 | 结构 CAD、装配、线束、电源、热设计、样件、环境预验证 | HW / ME | 是 |
| B. RF / Wireless / Certification | OP-04 + OP-11 中认证技术部分 | 地区化无线 BOM、天线布局、RF 预扫描、认证资料清单 | HW / SCM / LEG | 是 |
| C. Edge Platform & Device Firmware | OP-05 + OP-09 + OP-12 | Jetson 镜像、BSP、OTA、LoRa 服务、RTK/GNSS/IMU 融合服务 | EMB Lead | 是 |
| D. Application Software | OP-07 + OP-08 | 地图、任务、报告、Dashboard、视频 UI、告警面板 | FS Lead | M3 后启动 |
| E. AI Data & Model Optimization | OP-06 | 数据集、训练脚本、模型权重、TensorRT engine、评估报告 | AI Lead | 是 |
| F. Manufacturing & Test Fixtures | OP-10 | 试产 SOP、治具、老化测试、出厂测试、良率报告 | QA / SCM | M8/M9 后启动 |
| 内部核心包 | 架构/安全/接口/验收/合规边界 | API schema、数据模型、验收脚本、CCB、最终签署 | PM / Architect / QA | 全程 |

---

## 4. 一级包 SOW 边界

### A. Rugged Hardware & Mechatronics

| 项目 | 内容 |
|------|------|
| 包含 OP | OP-01 结构与工业设计；OP-02 电源、电池与热插拔；OP-03 热设计与环境预验证 |
| 范围 | Pelican 1450/1550 内部布局、支架、泡沫、面板、散热风道、防水穿舱件、Li-ion/LiFePO4 标准电池方案、专业版 LiPo 方案、BMS、DC-DC、受控热插拔、散热模组、高低温台架验证 |
| 输入 | 3D 模块尺寸、接口布局、电源树、热源位置、功耗 profile、续航目标、运输限制 |
| 输出 | STEP/2D 工程图、结构 BOM、线束图、电源原理图、BMS 配置、散热报告、样件、装配说明、测试报告 |
| 验收 | 装配无干涉；维护件可拆；受控热插拔有效；纹波满足 Jetson/传感器要求；+55°C 环境连续运行不宕机；整机 IP65 设计目标可测试 |
| 关键风险 | 结构、电源、热设计互相耦合，必须同包管理，避免三家供应商互相推责 |

### B. RF / Wireless / Certification

| 项目 | 内容 |
|------|------|
| 包含 OP | OP-04 RF/地区化 SKU/认证预审；OP-11 中无线、EMC、认证技术资料部分 |
| 范围 | LoRa/Wi-Fi/LTE/蓝牙/GNSS/卫星通信地区化 SKU、天线匹配、RF 预扫描、SRRC/FCC/CE RED/EMC 资料准备 |
| 输入 | 目标市场、通信需求、机械布局、天线位置、SKU 计划 |
| 输出 | 地区化无线 BOM、天线布局建议、预扫描报告、认证资料清单、风险项清单 |
| 验收 | 不使用“868/915MHz 通用”口径；CN/US/EU SKU 明确；RF/EMC 预扫描无阻塞项；认证路径和样机要求明确 |
| 与 OP-11 边界 | B 包提供技术资料和认证路径；OP-11 法务侧负责隐私、开源许可证、产品责任、出口/用途条款判断；最终 LEG 内部签署 |

### C. Edge Platform & Device Firmware

| 项目 | 内容 |
|------|------|
| 包含 OP | OP-05 Jetson BSP/系统镜像/OTA；OP-09 LoRa Mesh 协议与节点固件；OP-12 传感器与定位融合 |
| 范围 | JetPack 6.2.1、CUDA 12.6.10、NVMe 启动、Docker Compose、systemd、nvpmodel、OTA 回滚、LoRa 低速遥测、节点发现、RTK/GNSS/IMU 融合、NMEA/UBX 解析、NTRIP 接入、多摄像头同步触发 |
| 输入 | 计算模块、载板、外设清单、地区化通信模块、密钥管理策略、时间同步与坐标系约定、数据 schema |
| 输出 | 可刷写镜像、构建脚本、BSP 文档、OTA 测试报告、LoRa 协议文档、节点服务、定位融合服务、标定与精度报告 |
| 验收 | Orin Nano/NX 从 NVMe 启动；Lite/Standard/Pro 三档 Profile 可部署；LoRa 8 节点 24h 稳定且文件不走 LoRa；RTK 静态 1h 水平 StdDev <2cm、垂直 <3cm；多摄像头同步偏差 <5ms |
| 内部保留 | 安全架构、密钥策略、数据 schema、坐标系定义由内部冻结，C 包只实现和验证 |

### D. Application Software

| 项目 | 内容 |
|------|------|
| 包含 OP | OP-07 地图/导航/任务/报告；OP-08 Web UI / Dashboard |
| 范围 | MapLibre/MBTiles、离线地图缓存、轨迹记录、地理围栏、路径规划、TASK/SIM 任务管理、A/B 队伍现场状态模拟、时序回放、报告导出、Dashboard、视频窗口、节点状态、告警面板、用户权限 UI |
| 输入 | API 契约、数据模型、UI 规范、WebSocket 数据格式、地图源策略、AI 输出格式 |
| 输出 | 前后端模块代码、API 文档、测试用例、报告模板、组件库、UI 自动化测试 |
| 验收 | 本地地图 <5s 加载；任务 CRUD 与分配可用；时序回放 1–8×；报告 <30s 生成；地图/视频/告警/节点状态端到端显示；告警本地响应 <500ms |
| 端到端视频责任 | D 包负责 UI/前端渲染链路；E 包负责模型层；C 包负责设备侧取流与服务；**端到端视频 FPS 最终由内部 Integration Owner 牵头联合验收** |

### E. AI Data & Model Optimization

| 项目 | 内容 |
|------|------|
| 包含 OP | OP-06 AI 数据集、训练与 TensorRT 优化 |
| 范围 | 数据采集规范、标注、冻结验证集、模型训练、INT8 量化、TensorRT/DeepStream benchmark、评估报告 |
| 输入 | 类别定义、摄像头参数、热成像样本、授权策略、冻结测试集规范 |
| 输出 | 数据集说明、标注规范、训练脚本、模型权重、TensorRT engine、模型评估报告 |
| 验收 | 模型推理 ≥50 FPS（640×640, batch=1）；白天 mAP@0.5 ≥0.85；夜间/热成像 mAP@0.5 ≥0.70；报告 P/R/F1/误报/漏报/延迟 |
| 边界 | E 包只对模型层负责；端到端视频 FPS 由内部 Integration Owner 联合 C/D/E 验收；YOLOv8/Ultralytics 授权决策由内部 LEG/AI Lead 落定 |

### F. Manufacturing & Test Fixtures

| 项目 | 内容 |
|------|------|
| 包含 OP | OP-10 制造、测试工装与出厂测试 |
| 范围 | 试产 SOP、装配治具、老化测试、功能全检脚本、二维码/序列号、包装、FRU、备件清单 |
| 输入 | EVT2 设计、冻结 BOM、测试标准、包装要求、出厂验收脚本 |
| 输出 | SOP、工装、出厂测试报告模板、良率报告、备件安全库存建议、Pilot Batch 支持 |
| 验收 | Pilot Batch 50 套出厂测试 100% 通过；故障可追溯；FRU 更换流程可执行；良率报告完整 |
| 启动时机 | M8/M9 后启动；EVT2 之前只做 DFM 预审，不提前投入完整 NRE |

---

## 5. OP 二级 WBS 明细

| OP | 名称 | 所属一级包 | 是否建议单独发包 |
|----|------|------------|------------------|
| OP-01 | 结构与工业设计 | A | 否，归入 A |
| OP-02 | 电源、电池与热插拔 | A | 否，归入 A |
| OP-03 | 热设计与环境预验证 | A | 否，归入 A |
| OP-04 | RF、地区化 SKU 与认证预审 | B | 否，归入 B |
| OP-05 | Jetson BSP、系统镜像与 OTA | C | 否，归入 C |
| OP-06 | AI 数据集、训练与 TensorRT 优化 | E | 可作为独立一级包 E |
| OP-07 | 地图、导航、任务与报告软件 | D | 否，归入 D |
| OP-08 | Web UI / Dashboard | D | 否，归入 D |
| OP-09 | LoRa Mesh 协议与节点固件 | C | 否，归入 C |
| OP-10 | 制造、测试工装与出厂测试 | F | 可作为独立一级包 F |
| OP-11 | 合规、隐私与开源许可证审计 | B + 内部 LEG | 可拆咨询合同，但须由内部 LEG 管控 |
| OP-12 | 传感器与定位融合 | C | 否，归入 C；如找专业定位供应商，须由 C 包或内部 EMB Lead 统一接口 |

---

## 6. 端到端指标责任矩阵

| 指标 | 主责 | 协作 | 最终签署 |
|------|------|------|----------|
| 模型推理 FPS（640×640 ≥50） | E | C | AI Lead |
| 白天/夜间 mAP | E | QA | AI Lead / QA |
| 端到端视频 FPS（1080p ≥25） | 内部 Integration Owner | C + D + E | QA / System Architect |
| RTK 水平 <2cm / 垂直 <3cm | C | B + A | EMB Lead / QA |
| LoRa 8 节点 24h | C | B | EMB Lead / QA |
| IP65 设计目标 | A | B / F | HW Lead / QA |
| EMC Class A/B | B | A / C | HW Lead / LEG |
| 加密导出 | 内部安全 Owner | C + D | EMB Lead / FS Lead |
| Pilot Batch 50 套出厂测试 | F | A + C + D + E | QA / PM |

---

## 7. 并行开发节奏

| 阶段 | 内部主线 | 可并行外协 |
|------|----------|-------------|
| M1–M2 | 需求冻结、系统架构、接口定义、合规边界 | A 结构概念；B 认证/RF 预审；E 数据规范；OP-11 法务/SBOM 预审 |
| M2–M5 | POC 样机、Jetson 启动、核心传感器联调 | A 电源/热设计；B 地区化无线；C BSP/LoRa/RTK POC；E 数据集启动 |
| M5–M8 | Alpha 软件、接口联调、Lite/Standard/Pro 部署 | C 定位融合；D 地图/任务/Dashboard；E 模型优化；B RF 预扫描 |
| M8–M11 | EVT/EVT2、整机集成、环境预测试 | A 环境预验证；B EMC 预测试；F 测试工装/DFM |
| M11–M15 | 认证、Pilot Batch、文档包 | B 认证支持；F 试产；OP-11 合规文件 |
| M16–M18 | Pilot 反馈、PVT、GA 准备 | F 良率优化；A 结构修订；E 模型迭代；D UI/报告优化 |

---

## 8. 合同与付款建议

| 一级包 | 合同方式 | 付款建议 |
|--------|----------|----------|
| A 硬件/机电 | 固定范围 SOW + 样件/测试里程碑 | 30% 启动 / 40% EVT 样件和报告 / 30% 验收 |
| B RF/认证 | 咨询 + 预扫描 + 认证支持 | 30% 启动 / 40% 预扫描/资料 / 30% 认证路径确认 |
| C 设备平台/固件 | 里程碑交付 + 可复现构建验收 | 30% 启动 / 40% POC 镜像与服务 / 30% 集成验收 |
| D 应用软件 | Sprint + API 合同测试 | 每 2–3 周验收一次可运行版本，保留尾款到系统联调 |
| E AI | 数据集冻结 + 模型指标验收 | 数据规范/标注/模型达标/推理优化分段付款 |
| F 制造测试 | NRE + 单台加工/组装费 | NRE 按治具/SOP 验收，单台按合格出货结算 |

---

## 9. 接口治理规则

1. 所有一级包必须基于冻结的 API schema、数据模型、硬件接口图、无线 SKU 矩阵和测试标准开发。
2. 供应商不得单方面变更接口、无线频段、电池方案、数据格式、坐标系、时间同步或安全策略。
3. 接口变更必须提交 CCB，说明影响范围、兼容性、测试计划和回滚策略。
4. 所有交付物必须入库：源代码、构建脚本、原理图、CAD、BOM、测试日志、报告、许可证清单。
5. 外协交付必须可复现：内部团队应能在本地重新构建、重新刷写、重新测试。
6. SOW / RFP 必须同时引用 v1.3.2 覆盖层和对应 v1.3 明细文档，并列明适用章节；不得只引用单一文件。

---

## 10. 最小内部团队配置建议

| 角色 | 人数 | 责任 |
|------|------|------|
| PM / Product Owner | 1 | 需求、分包管理、预算、里程碑、客户试点 |
| System Architect / Tech Lead | 1 | 架构、接口、技术取舍、集成问题裁决 |
| Embedded Lead | 1 | Jetson、BSP、驱动、系统服务、硬件联调 |
| Full-stack Lead | 1 | API、数据模型、Dashboard 集成、报告系统 |
| AI Lead | 1 | 数据、模型、评估、推理优化验收 |
| QA / Integration | 1 | 验收脚本、测试计划、缺陷追踪、出厂测试、端到端指标签署 |
| Legal/Compliance | 外部顾问 + 内部 PM 对接 | 合规、许可证、用户协议、认证资料 |

---

## 11. 外协风险与控制措施

| 风险 | 影响 | 控制措施 |
|------|------|----------|
| 一级包过多 | PM 与架构师被供应商协调拖垮 | 对外只发 A–F，OP 作为内部 WBS |
| 接口失控 | 模块无法集成 | API/硬件接口冻结，变更走 CCB |
| 外协只交 Demo 不交可维护资产 | 后续无法量产 | 合同写明源码、脚本、CAD、BOM、测试日志、文档必须交付 |
| AI 指标不可复现 | 验收争议 | 冻结测试集、固定 benchmark 条件、内部复测 |
| 端到端视频 FPS 无主责 | OP-06/08 互相推责 | 内部 Integration Owner 牵头，C/D/E 联合验收 |
| RF/电池地区合规遗漏 | 认证失败或无法运输 | B 包 + OP-11 前置，地区化 SKU 明确 |
| 结构、电源、热设计互相冲突 | 返工 | A 包合并管理，M2 前完成机械/电源/热联合评审 |
| 安全实现外包后不可审计 | 数据与密钥风险 | 安全架构内部设计，外协实现必须代码审查和渗透测试 |

---

## 12. 推荐启动顺序

第一批启动（M1–M2）：

1. A. Rugged Hardware & Mechatronics。
2. B. RF / Wireless / Certification。
3. E. AI Data & Model Optimization。
4. OP-11 法务、隐私、开源许可证审计（由内部 LEG 管控）。

第二批启动（M2–M5）：

1. C. Edge Platform & Device Firmware。
2. A 包内电源/热样件深化。
3. B 包 RF 预扫描准备。

第三批启动（M3–M8）：

1. D. Application Software。
2. C 包定位融合与 LoRa 稳定性验证。
3. E 包模型优化与冻结测试集评估。

后置启动（M8/M9 以后）：

1. F. Manufacturing & Test Fixtures。
2. 认证实验室正式送测支持。

---

## 13. 一句话执行建议

MSkit 不应按 12 个 OP 直接外包，而应按 **6 个一级合同包 + 内部核心包** 管理；OP-01–OP-12 保留为二级 WBS、验收点和风险跟踪项。这样可以同时保证并行开发、合同可控、接口清晰和最终整机责任不外溢。
