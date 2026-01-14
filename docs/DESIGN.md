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
*   **职责**: 系统的“大脑”。负责加载配置，按顺序初始化仪表，执行场景。

#### 2.1.1 时间轴调度引擎 (Timeline Engine)
系统采用**基于时间偏移 (Time-Offset)** 的调度机制，以模拟真实的动态电磁环境。
1.  **事件调度 (Event Dispatcher)**: 在测试启动 (T=0) 后，根据场景定义在特定的时间偏移点向 HAL 发送控制指令。
2.  **并发采样 (Continuous Monitor)**: 后台任务以固定频率（如 10Hz）轮询性能指标。
3.  **时间同步**: 所有日志和采样数据挂载统一的“场景相对时间戳”。

#### 2.1.2 混合编排架构 (Hybrid Orchestration)
为了兼顾“动态仿真”与“参数扫描”两类截然不同的测试需求，Sequencer 实现了策略分发模式：
1.  **Timeline Strategy (时间轴策略)**: 适用于动态场景。开环控制，强调动作的准时性。
2.  **Algorithm Strategy (算法策略)**: 适用于灵敏度/阻塞搜索。闭环反馈，强调结果的收敛性。

### 2.2 硬件抽象层 (HAL) - 驱动架构
系统采用 **驱动工厂模式 (Driver Factory Pattern)** 来实现“上层指令单一，底层自动适配”的设计目标。

#### 2.2.1 架构分层
1.  **统一接口层 (Proxy)**: 业务逻辑调用的对象 (如 `VSG`)。负责维护连接并转发调用。
2.  **驱动工厂 (Factory)**: 执行 `connect` -> `query(*IDN?)` -> 匹配并实例化对应的驱动类。
3.  **具体实现层 (Implementation)**: 继承自 `Generic` 基类，实现标准接口。

### 2.3 手册库 (Manual Library)
*   **位置**: `backend/manual_library/`
*   **职责**: 集中管理所有硬件的编程手册。
*   **设计原则**: Catalog-Driven 扫描，严格级联上传，智能过滤展示。

### 2.4 仪表能力描述 (HAL Specs)
*   **位置**: `backend/drivers/hal_specs/`
*   **用途**: 运行时能力校验 (Capability Check)、GUI 边界限制、驱动元数据定义。

### 2.5 开发规范 (Development Standards)
为了避免运行时环境错误和集成问题，所有代码开发需遵循以下硬性标准：
1.  **绝对导入 (Absolute Imports)**: 必须使用基于根包的绝对导入。
2.  **API 路由与前缀**: 所有后端接口必须挂载在版本号前缀下 (如 `/api/v1/...`)。
3.  **环境隔离**: 所有手动 CLI 操作前，必须先验证虚拟环境 (`venv`) 是否激活。

### 2.6 仪表接口标准化规范 (Standardized Instrument Interfaces)
为了实现“硬件无关”的编排逻辑，HAL 层必须遵循严格的接口契约和生命周期流程。

#### 2.6.1 标准生命周期 (Lifecycle)
所有驱动在 `connect()` 和 `disconnect()` 时必须执行以下标准动作：
*   **连接 (Connect)**:
    1.  `OPEN`: 建立物理层 VISA 连接。
    2.  `IDENTIFY`: 发送 `*IDN?` 并缓存。
    3.  `RESET`: 发送 `*RST` 恢复默认（可选）。
    4.  `CLEAN`: 发送 `*CLS` 清除错误。
*   **断开 (Disconnect)**:
    1.  `STOP`: 停止射频发射。
    2.  `CLOSE`: 释放资源。

#### 2.6.2 信道模拟器标准方法 (Channel Emulator API)
每个驱动必须实现：
*   `load_channel_model(name)`: 加载场景模型。
*   `rf_on() / rf_off()`: 射频开关。
*   `set_velocity(kmh)`: 设置多普勒速度。
*   `set_input_power(dbm)`: 设置输入期望电平。

#### 2.6.3 信号发生器标准方法 (VSG API)
*   `set_frequency(hz)`: 设置中心频率。
*   `set_power(dbm)`: 设置幅度。
*   `enable_output(bool)`: RF 开关。
*   `load_waveform(filename)`: 加载 ARB 波形。

## 3. GUI 设计方案 (已实施)

### 3.1 技术栈
*   **前端**: React (TypeScript) + Vite + Material UI (MUI)。
*   **后端**: FastAPI (Python 3.13) + Uvicorn。

### 3.2 已实现功能
1.  **仪表盘 (Dashboard)**: 状态卡片、实时日志、场景选择执行。
2.  **手册库 (Manuals)**: 手册浏览、在线预览、级联上传。

## 4. 下一步实施计划
1.  **实时数据可视化**: 前端增加吞吐量实时折线图。
2.  **配置编辑器**: 实现 `config.yaml` 的 GUI 可视化修改。
3.  **DUT 深度集成**: 利用 ADB 抓取 Modem 内部参数。

## 5. 核心业务场景 (Core Use Cases)
### 5.1 灵敏度测试 (Sensitivity Search)
*   **实现**: 算法策略。闭环扫描下行功率，通过 BLER 反馈寻找临界点。
### 5.2 阻塞干扰分析 (Blocking Analysis)
*   **实现**: 混合策略。VSG 扫描干扰频点和功率，监测吞吐量损失。
### 5.3 动态衰落场景 (Dynamic Fading)
*   **实现**: 时间轴策略。动态模拟高铁速度变化和场景切换。
