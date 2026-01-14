# Gemini 助手项目指南 (GEMINI.md)

## 1. 基本原则
*   **语言**: 所有的对话、解释、代码注释和文档必须使用 **简体中文**。
*   **角色**: 你是一个专业的软件工程师，负责维护和扩展“终端宽带标准信道验证系统”。

## 2. 项目概述
本项目是一个自动化测试框架，用于编排和执行涉及多种射频仪表（VNA, VSG, 信道模拟器, 综合综测仪, 频谱仪）和被测件（DUT）的宽带信道验证测试。
*   **核心语言**: Python 3
*   **架构**: 分层架构 (Sequencer -> HAL -> Drivers)。
*   **关键特性**: 支持全链路“模拟模式 (Simulation Mode)”，允许在无硬件环境下开发。

## 3. 编码规范
*   **风格**: 遵循 PEP 8 标准。
*   **类型提示**: 所有函数和方法必须包含 Type Hints (例如 `def connect(self) -> None:`)。
*   **文档**: 使用 Google Style Docstrings。
*   **异常处理**: 严禁裸露的 `try...except`，必须捕获特定异常并记录日志。
*   **日志**: 使用 `core.logger` 模块，禁止使用 `print()`。

## 4. 开发工作流
1.  **优先模拟**: 在修改驱动或核心逻辑后，首先运行 `python3 main.py --simulate` 验证逻辑通顺。
2.  **模块化**: 保持 `drivers/` 目录下的仪表驱动独立且接口一致（继承自 `BaseInstrument`）。
3.  **配置驱动**: 所有的硬编码参数（IP 地址、频率范围等）应移至 `config.yaml`。
4.  **验证**: 使用 `tests/` 目录下的单元测试（如果有）进行回归测试。

## 5. 架构演进规划 (GUI)
我们计划引入 GUI，技术栈如下：
*   **前端**: React + Material UI (MUI)
*   **后端**: FastAPI
*   **通信**: REST API + WebSocket
*   **详情**: 参见 `docs/DESIGN.md`。

## 6. 特定指令
*   在创建新文件时，自动检查目录是否存在，必要时创建。
*   对于复杂的重构任务，先生成设计或变更计划。
*   **硬件驱动开发铁律 (Evidence-Based Driver Development)**:
    1.  **先查后写**: 在编写任何仪表控制代码 (SCPI/ATE) 之前，必须先查阅 `backend/manual_library`。
    2.  **提取证据**: 使用 `backend/manual_library/extract_pdf_info.py` 或 `read_file` 工具定位具体指令语法。
    3.  **引用来源**: 在代码注释中必须明确引用来源手册及页码（例如: `Ref: Vertex User Guide, p.243`）。
    4.  **拒绝猜测**: 严禁凭空猜测指令。如果不确定，必须标记为 TODO 并要求上传手册。
*   **开发避坑指南 (Lessons Learned)**:
    1.  **环境一致性**: 在执行任何 Python 命令前，必须显式检查 `source venv/bin/activate`。不要假设环境是就绪的。
    2.  **导入安全性**: 项目内部模块引用**强制使用绝对导入** (Absolute Imports)，禁止使用 `..` 相对导入，以避免 `ImportError`。
*   **接口对齐**: 前后端对接时，必须双向核对 URL 全路径（特别是 `/api/v1` 前缀），禁止仅凭借觉写路径。
*   **时间轴中心原则 (Time-Centric Logic)**:
    1.  **偏移驱动**: 复杂的测试逻辑必须定义为相对于起始点 (T=0) 的事件序列。
    2.  **非阻塞执行**: 严禁在测试循环中使用长周期的同步 `time.sleep`；必须使用异步任务调度，以确保数据采集与硬件控制能够并行。
    3.  **时间戳对齐**: 所有采集到的指标（Throughput, BLER 等）必须附带场景相对时间戳，确保数据与事件在时间轴上严格对齐。
*   **测试逻辑分层原则 (Logic Stratification)**:
    1.  **各司其职**: 不要试图在时间轴引擎 (Timeline Engine) 中硬塞复杂的 `if/else` 反馈逻辑；遇到闭环控制需求（如灵敏度搜索），请创建独立的算法策略类。
    2.  **统一入口**: 所有的测试执行必须通过 `run_test_case` 分发器，根据 `type` 字段自动选择正确的引擎，禁止绕过分发器直接调用底层逻辑。

## 7. 关键仪表指令集参考 (Verified SCPI Checklist)
**重要原则**: 在实施驱动代码前，必须查阅 `backend/manual_library` 中的本地手册确认语法正确性。

### 7.1 R&S SMW200A (信号发生器)
*   [x] **频率设置**: `SOURce:FREQuency:CW <freq>` (通用) 或 `FREQ <freq>`
*   [x] **功率设置**: `SOURce:POWer:LEVel:IMMediate:AMPLitude <dbm>`
*   [x] **波形选择**: `SOURce:BB:ARBitrary:WAVeform:SELect '<path>'` (路径如 `/var/user/mywave.wv`)
*   [x] **ARB 开启**: `SOURce:BB:ARBitrary:STATe ON`
*   [x] **射频开启**: `OUTPut:STATe ON`
*   [ ] **5G NR 配置 (可选)**: `SOURce:BB:NR5G:...` (需参考 SMW200A User Manual)

### 7.2 R&S FSW (频谱分析仪)
*   [x] **中心频率**: `SENSe:FREQuency:CENTer <freq>`
*   [x] **Span 设置**: `SENSe:FREQuency:SPAN <span_hz>`
*   [x] **参考电平**: `DISPlay:WINDow:TRACe:Y:SCALe:RLEVel <dbm>`
*   [x] **Peak Search**: `CALCulate:MARKer1:MAXimum:PEAK`
*   [x] **读取 Marker**: `CALCulate:MARKer1:Y?`
*   [ ] **截图获取**: `HCOPy:DESTination 'MMEM'`; `HCOPy:DEVice:LANGuage PNG`; `HCOPy:IMMediate`

### 7.3 R&S CMW500 (综合测试仪)
*   *注意: CMW500 涉及复杂的信令状态机，建议优先使用 "CMWcards" 或 Python 库 `RsCmwBase` 封装，裸 SCPI 较为繁琐。*
*   [ ] **进入 LTE 信令**: `ROUTe:SIGNaling:LTE:SCENario:MODe STANdard`
*   [ ] **设置下行频率**: `CONFigure:LTE:SIGNaling:DL:PCC:FREQuency <freq>`
*   [ ] **开启信令**: `SOURce:LTE:SIGNaling:STATe ON`
*   [ ] **查询连接状态**: `FETCh:LTE:SIGNaling:PSWitched:STATe?` (期望返回 'ATTached')

### 7.4 R&S ZNA (网络分析仪)
*   [x] **预置**: `SYSTem:PRESet`
*   [x] **定义 Trace**: `CALCulate:PARameter:DEFine '<TraceName>', 'S21'`
*   [x] **显示 Trace**: `DISPlay:WINDow1:TRACe1:FEED '<TraceName>'`
*   [x] **单次扫描**: `INITiate:IMMediate; *WAI`
*   [x] **读取数据**: `CALCulate:DATA? FDATa` (返回格式化的实数数组)
