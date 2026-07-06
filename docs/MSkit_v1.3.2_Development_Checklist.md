# MSkit v1.3.2 开发 Checklist 同步版

> **基线**：`MSkit_v1.3.2_Spec.md`｜**用途**：替代历史 `MSkit_v1.3_Development_Checklist.md` 中与 v1.3.2 不一致的条目。

---

## Phase 1: 需求与合规

- [ ] v1.3.2 Spec 签署：PM + 技术负责人 + 法务。
- [ ] 术语表审查：统一为“避免军用采购、武器化与作战用途表述”。
- [ ] SKU 命名审查：对外材料优先使用 Team / Field，不突出 Command。
- [ ] YOLOv8/Ultralytics 授权决策：Enterprise License 或替换宽松许可框架。
- [ ] 地区化无线 SKU 矩阵确认：CN / US / EU。
- [ ] 电池运输合规路径确认：空运、陆运、仓储、保险、退换货。

## Phase 2: 硬件与通信

- [ ] JetPack 6.2.1 + CUDA 12.6.10 启动验证。
- [ ] Orin Nano/NX 从 NVMe 启动；不得写板载 64GB eMMC。
- [ ] RTK/GNSS + IMU 定位融合：静态 1h 水平 StdDev <2cm、垂直 <3cm；多摄像头同步偏差 <5ms（K4，P0，OP-12）。
- [ ] LoRa 仅验收位置、状态、告警、短文本；文件传输走 Wi-Fi/USB/以太网。
- [ ] LoRa 模块和天线按目标市场频段采购，不写“868/915MHz 通用”。
- [ ] LTE 模块按目标市场选型，不默认 EC25-EU 覆盖所有地区。
- [ ] 标准版电池优先评估 Li-ion/LiFePO4；LiPo 仅限工程样机/专业用户版本。
- [ ] 受控热插拔验证：低功耗保护、反接、防火、温度、过流和机械锁止。

## Phase 3: 软件与 AI

- [ ] Lite / Standard / Pro 三档 Profile 分层部署验证。
- [ ] 模型推理 FPS：640×640, batch=1, INT8, TensorRT/DeepStream，YOLOv8n ≥50 FPS。
- [ ] 端到端视频 FPS：1080p 输入，含解码、resize、推理、跟踪、叠加、WebSocket 输出，单路 ≥25 FPS。
- [ ] 白天检测 mAP@0.5 ≥0.85，冻结测试集 ≥5,000 张。
- [ ] 夜间/热成像 mAP@0.5 ≥0.70，冻结测试集 ≥3,000 张。
- [ ] 报告 Precision / Recall / F1 / 误报率 / 漏报率 / 端到端延迟。
- [ ] 加密导出：默认输出接收方公钥加密包；导出前需 PIN/FIDO2/本地账户二次确认。

## Phase 4: 无人机与外设

- [ ] MVP 仅支持 DJI 日志/媒体导入与视频流桥接。
- [ ] 控制类集成标记为 Phase 2，不纳入 MVP 验收。
- [ ] Remote ID 仅显示/记录状态；不替代运营方合规义务。
- [ ] MAVLink 接口只验收遥测读取；控制类动作需 PoC 与安全评审后单独冻结。

## Phase 5: 环境、EMC 与认证

- [ ] IP65/IP67 为整机装配后目标等级；开孔完成后做 IEC 60529 整机测试。
- [ ] MIL-STD-810H 仅作为设计验证方法；第三方报告前不宣称 certified。
- [ ] EMC 按 SKU 拆分：消费/户外目标 Class B，工业/商用可 Class A。
- [ ] UN38.3 测试摘要收集；>300Wh 电池按危险品运输流程评估。
- [ ] RoHS/REACH/WEEE、EN/UL 62368-1、SRRC/FCC/CE 资料齐备。

## Phase 6: 交付与文档

- [ ] README、Spec、BOM、Development Plan、Checklist 均同步 v1.3.2 口径。
- [ ] 三个附属图入库或标记“待补充，未入库前不得作为规格完整性交付项”。
- [ ] Pilot Batch 50 套不承担全部研发摊销；商业模型按 300–500 套重算。
- [ ] v1.4 冻结前完成供应商 RFQ、样品验证、法律审查、系统功耗测试和认证预测试。
