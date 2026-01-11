# 终端宽带标准信道验证系统 - 设计方案

## 1. 系统概述

本项目旨在提供一个自动化框架，用于编排和执行涉及多种射频仪表（VNA, VSG, 信道模拟器, 综合综测仪, 频谱仪）和被测件（DUT, 如 Android 终端）的宽带信道验证测试。系统支持灵活的测试流程定义、硬件抽象控制以及全链路模拟模式。

### 1.1 核心架构
系统采用 **分层架构 (Layered Architecture)**，自下而上分为：

1.  **基础设施层**: 日志、配置加载、通用工具。
2.  **硬件抽象层 (HAL)**: 封装 PyVISA 和 ADB，屏蔽不同厂商仪表的指令差异，提供统一的 Python API。支持“模拟模式”以脱离硬件开发。
3.  **业务逻辑层**: `TestSequencer` 负责解析测试用例，协调各仪表和 DUT 的动作，执行测试流程。
4.  **接口层 (B/S架构)**: 
    *   **Backend**: 基于 **FastAPI** 的 RESTful API 服务，负责硬件控制和数据分发。
    *   **Frontend**: 基于 **React + Material UI** 的单页应用 (SPA)，提供可视化监控和控制。

```mermaid
graph TD
    User[用户] --> Frontend[前端 (React)]
    Frontend -->|REST API / WebSocket| Backend[后端 (FastAPI)]
    
    Backend --> Core[业务逻辑层 (Sequencer)]
    Backend --> Manuals[手册库服务]
    
    Core --> HAL[硬件抽象层 (Drivers)]
    Core --> DUT_Mgr[DUT 管理 (ADB)]
    
    HAL --> VNA[矢量网络分析仪]
    HAL --> VSG[矢量信号发生器]
    HAL --> CE[信道模拟器]
    HAL --> SA[频谱仪]
    
    DUT_Mgr --> Android[Android 终端]
    
    Config[config.yaml] --> Core
```

## 2. 现有模块详解

### 2.1 编排器 (Sequencer)
*   **位置**: `backend/core/sequencer.py`
*   **职责**: 系统的“大脑”。负责加载配置，按顺序初始化仪表，循环执行 `test_cases` 列表中定义的测试步骤。

### 2.2 硬件抽象层 (HAL) - 驱动架构
系统采用 **驱动工厂模式 (Driver Factory Pattern)** 来实现“上层指令单一，底层自动适配”的设计目标。这意味着业务代码无需关心具体的仪器型号，完全由 HAL 动态解析。

#### 2.2.1 架构分层
HAL 自上而下分为三层：

1.  **统一接口层 (Proxy)**:
    *   **角色**: 业务逻辑直接调用的对象 (如 `VSG`, `VNA`)。
    *   **职责**: 暴露标准 API (如 `set_frequency`)。它不包含 SCPI 指令，而是负责维护连接，并在连接成功后调用 **工厂** 获取具体的驱动实例，将操作转发给该实例。
2.  **驱动工厂 (Factory)**:
    *   **职责**: 连接设备 -> 发送 `*IDN?` -> 匹配厂商和型号 -> 实例化对应的驱动类。
    *   **注册表**: 维护 `IDN 字符串` 到 `驱动类` 的映射关系。
3.  **具体实现层 (Implementation)**:
    *   **角色**: 真正的干活代码 (如 `RS_SMW200A_Driver`)。
    *   **职责**: 继承自 `BaseDriver`，实现标准接口，将通用意图翻译为该型号特有的 SCPI 指令。

#### 2.2.2 目录结构
```text
backend/drivers/
├── __init__.py           # 暴露通用代理类 (VSG, VNA)
├── factory.py            # 驱动工厂逻辑
├── base/                 
│   ├── driver_interface.py # 定义标准接口 (抽象基类)
│   └── scpi_common.py      # 通用 SCPI 实现 (默认回退)
├── rohde_schwarz/        # R&S 专用驱动
│   ├── smw200a.py
│   ├── fsw.py
│   └── cmw500.py
├── keysight/             # Keysight 专用驱动
│   ├── mxg.py
│   └── pna.py
└── ...                   # 其他品牌
```

#### 2.2.3 如何添加新仪表
当需要支持一款不在列表中的新仪表（例如 Tektronix 示波器）时：
1.  **创建驱动文件**: 在 `backend/drivers/tektronix/` 下新建 `oscilloscope.py`。
2.  **实现接口**: 继承 `BaseOscilloscopeDriver`，实现 `capture_waveform` 等方法。
3.  **注册**: 在 `backend/drivers/factory.py` 的注册表中添加一行：
    ```python
    "TEKTRONIX,MSO5": "drivers.tektronix.oscilloscope.MSO5_Driver"
    ```
4.  **完成**: 无需修改任何核心业务代码，系统连接到该设备时会自动加载新驱动。

#### 2.2.4 驱动开发标准流程 (SOP)
为确保对硬件操作的准确性，必须遵循以下闭环流程：
1.  **手册入库**: 通过 GUI "手册库" 页面上传厂商提供的编程手册 (PDF)。
2.  **指令提取**: 使用工具脚本 `backend/manual_library/extract_pdf_info.py` 扫描 PDF，提取 "Remote Control", "SCPI", "ATE" 等章节。
3.  **语法核实**: 确认关键指令（如 `LOAD`, `INIT`, `*OPC?`）的准确语法（是否带引号、参数分隔符等）。
4.  **代码实现**: 编写驱动代码，并在关键方法上**注明手册来源和页码**。
5.  **模拟验证**: 在模拟模式下，通过构造伪造的 `*IDN?` 响应来触发新驱动加载，验证逻辑链路。

### 2.3 手册库 (Manual Library)
*   **位置**: `backend/manual_library/`
*   **职责**: 集中管理所有硬件的编程手册。
*   **索引**: `catalog.yaml` 是核心索引，定义了仪表类型、厂商、系列和下载链接。
*   **设计原则**:
    *   **Catalog-Driven**: 本地文件扫描逻辑由 Catalog 驱动。系统根据 Catalog 定义的厂商/系列名构建预期路径，去文件系统中查找文件，而不是反向推断。这解决了文件夹命名（如包含 `&` 符号）不一致的问题。
    *   **严格上传**: 前端上传必须通过级联选择器（Type -> Vendor -> Series），禁止用户手动输入厂商系列名，保证目录结构与 Catalog 一致。
    *   **智能展示**: 前端会自动检测本地是否存在手册。如果存在，会自动隐藏“需登录/不可用”的占位符条目，优先展示本地文件。

### 2.4 仪表能力描述 (HAL Specs)
*   **位置**: `backend/drivers/hal_specs/`
*   **格式**: JSON
*   **用途**:
    1.  **运行时能力校验 (Capability Check)**: 在测试开始前，对比测试用例的需求（如频率 50GHz）与仪表 Profile（如最大 6GHz），提前拦截不兼容的配置。
    2.  **GUI 边界限制**: 为前端提供参数验证规则（如最小/最大功率），改善用户体验。
    3.  **驱动元数据 (Metadata)**: 描述驱动支持的高级特性（如 "Support_5G_NR": true），供业务层动态决策。

### 2.5 开发规范 (Development Standards) **[New]**
为了避免运行时环境错误和集成问题，所有代码开发需遵循以下硬性标准：
1.  **绝对导入 (Absolute Imports)**:
    *   严禁在跨子模块引用时使用相对导入 (如 `from ..common import ...`)。
    *   必须使用基于根包的绝对导入 (如 `from drivers.common.generic_ce import ...`)，以确保在不同启动上下文中路径解析的一致性。
2.  **API 路由与前缀**:
    *   所有后端接口（包括 WebSocket）必须挂载在版本号前缀下 (如 `/api/v1/...`)。
    *   前端代码禁止硬编码无前缀的 URL，必须与后端路由表保持严格一致。
3.  **环境隔离**:
    *   所有手动 CLI 操作前，必须先验证虚拟环境 (`venv`) 是否激活。推荐使用项目根目录下的 `./start_system.sh` 脚本，它内置了环境检查逻辑。

## 3. GUI 设计方案 (已实施)

目前系统已完成基础 GUI 框架的搭建。

### 3.1 技术栈
*   **前端**: React (TypeScript) + Vite + Material UI (MUI)。
*   **后端**: FastAPI (Python 3.13) + Uvicorn。
*   **通信**: Axios (REST API)。

### 3.2 功能模块规划

#### A. 仪表盘 (Dashboard) & 连接管理
*   **状态卡片**: 显示所有已配置仪表的连接状态 (在线/离线/模拟)。
*   **一键操作**: 提供“连接所有”、“断开所有”按钮。
*   **Ping 检测**: 后台定期检测仪表心跳。

#### A.1 仪表详情与驱动诊断 (Instrument Details) **[New]**
为了配合后端的 **驱动工厂模式**，前端需要提供深度的诊断信息：
*   **驱动信息**: 在详情弹窗中显示当前加载的驱动类名 (e.g., `RS_SMW200A_Driver`) 和文件路径。
*   **IDN 原始数据**: 显示设备返回的原始 `*IDN?` 字符串，方便排查识别问题。
*   **能力列表**: 列出当前驱动支持的特性 (Capabilities)，如 `Is Vector Source`, `Supports 5G NR`。
*   **驱动覆盖 (Override)**: 允许用户在配置中强制指定使用某个通用驱动 (Generic SCPI) 而非自动匹配的专用驱动，以应对兼容性问题。

#### B. 测试配置器 (Test Configurator)
*   **可视化编辑**: 将 `config.yaml` 映射为表单。
*   **用例管理**: 允许用户添加、删除测试步骤，拖拽调整顺序。
*   **参数校验**: 前端对频率范围、IP 格式等进行实时校验。

#### C. 执行监控 (Execution Monitor)
*   **进度条**: 显示当前测试用例的总体进度。
*   **步骤高亮**: 高亮显示当前正在执行的操作（如“正在配置 VNA...”, “正在运行流量...”）。
*   **实时日志**: 一个类似终端的窗口，实时滚动显示后端日志（支持按级别过滤：INFO/ERROR）。

#### D. 数据可视化 (Data Visualization)
*   **吞吐量曲线**: 实时绘制吞吐量 vs 时间图表。
*   **频谱视图**: 如果频谱仪支持，定期抓取屏幕截图或 Trace 数据并在前端渲染。

### 3.3 API 设计 (部分)

#### `GET /api/v1/instruments/status`
返回所有仪表的实时状态，新增 `driver_info` 字段：
```json
[
  {
    "id": "vsg",
    "name": "R&S SMW200A",
    "connected": true,
    "driver_info": {
      "idn": "Rohde&Schwarz,SMW200A,100101,4.70...",
      "loaded_driver": "RS_SMW200A_Driver",
      "driver_file": "backend.drivers.rohde_schwarz.smw200a"
    }
  }
]
```

### 3.4 目录结构 (当前)

```text
/
├── backend/                # 后端 (Python)
│   ├── app/                # FastAPI 应用
│   │   ├── api/            # 路由定义
│   │   └── main.py         # 服务入口
│   ├── core/               # 核心逻辑
│   ├── drivers/            # 仪表驱动 (Factory Pattern)
│   ├── manual_library/     # 手册库及工具脚本
│   └── requirements.txt
├── frontend/               # 前端 (React)
│   ├── src/
│   │   ├── pages/          # 页面组件 (Dashboard, Manuals)
│   │   ├── theme.ts        # 全局主题定义
│   │   └── App.tsx         # 路由配置
│   └── package.json
└── start_system.sh         # 一键启动脚本
```

## 4. 下一步实施计划

1.  **Phase 1 (Done)**: 基础架构搭建 (FastAPI + React)，手册库功能上线。
2.  **Phase 2 (In Progress)**: **硬件驱动重构 (Factory Pattern)**。
    *   建立 `drivers/base`, `drivers/rohde_schwarz` 目录结构。
    *   实现 `DriverFactory` 和 `*IDN?` 自动识别逻辑。
    *   迁移 VSG, VNA 等驱动到新架构。
3.  **Phase 3**: **GUI 适配与增强**。
    *   更新后端 API 以返回 `driver_info`。
    *   前端 Dashboard 增加详情页，展示驱动加载情况。
4.  **Phase 4**: **业务逻辑完善**。
    *   实现“开始测试”控制流。
    *   实现测试日志的 WebSocket 推送。