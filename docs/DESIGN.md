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

## 4. 开发路线图 (Roadmap)

本项目采用分阶段迭代开发。Phase 1-6 已完成，Phase 7 正在规划中。

### 4.1 Phase 1: 实时数据可视化 ✅ 已完成
*   **目标**: Dashboard 实时展示测试过程中的吞吐量和 BLER 数据。
*   **技术方案**:
    *   扩展 WebSocket 增加 `metrics` 消息类型
    *   前端集成 `recharts` 折线图，维护60秒滑动窗口
*   **涉及文件**: `endpoints.py`, `sequencer.py`, `Dashboard.tsx`, `log_manager.py`

### 4.2 Phase 2: 测试结果存储 ✅ 已完成
*   **目标**: 持久化测试结果，支持历史查询。
*   **技术方案**:
    *   SQLite 数据库，表: `test_runs`, `metrics_samples`
    *   新增 `/api/v1/history` 查询接口
*   **涉及文件**: `database.py`, `History.tsx`

### 4.3 Phase 3: 报告生成引擎 ✅ 已完成
*   **目标**: 测试完成后自动生成 PDF 报告。
*   **技术方案**:
    *   Jinja2 HTML 模板 + weasyprint 渲染 PDF
    *   新增 `/api/v1/report/{run_id}/html` 和 `/api/v1/report/{run_id}/pdf` 接口
*   **涉及文件**: `report_generator.py`, `templates/report.html`

### 4.4 Phase 4: 配置编辑器 ✅ 已完成
*   **目标**: 前端可视化编辑 `config.yaml` 和场景文件。
*   **技术方案**:
    *   后端 `/api/v1/config` 读写接口
    *   前端代码编辑器 (YAML 语法高亮)
*   **涉及文件**: `endpoints.py`, `ConfigEditor.tsx`

### 4.5 Phase 5: 单元测试完善 ✅ 已完成
*   **目标**: pytest 覆盖率 > 70%。
*   **涉及文件**: `tests/test_sequencer.py`, `tests/test_drivers.py`, `tests/test_api.py`, `tests/test_database.py`, `tests/test_report_generator.py`

### 4.6 Phase 6: DUT 深度集成 ✅ 已完成
*   **目标**: 抓取 Android Modem 内部参数 (RSRP/RSRQ/SINR/CQI)。
*   **技术方案**: 解析 `dumpsys telephony.registry` 输出
*   **新增 API**:
    *   `GET /api/v1/dut/status` - DUT 连接状态
    *   `GET /api/v1/dut/modem` - Modem 详细参数
    *   `GET /api/v1/dut/signal` - 信号质量摘要
    *   `POST /api/v1/dut/airplane-mode` - 飞行模式控制
*   **涉及文件**: `android_controller.py`, `endpoints.py`

### 4.7 Phase 7: 前端界面增强 ✅ 已完成
*   **目标**: 增强前端可视化能力，完善 DUT 监控及用户体验。
*   **子任务**:
    1.  **DUT 状态面板**: 在 Dashboard 展示 Android 终端的 Modem 参数 (RSRP/RSRQ/SINR/CQI) 和飞行模式控制。
    2.  **测试进度可视化**: 实时展示测试执行进度条和事件时间轴。
    3.  **主题切换**: Support Light/Dark mode.
    4.  **ConfigEditor 升级**: 集成 Monaco Editor，支持 YAML Schema 自动补全和校验。✅ 已完成亮色主题切换，并持久化用户偏好。
*   **技术方案**:
    *   新建 `DutPanel.tsx`, `TestProgress.tsx` 组件
    *   新建 `ThemeContext.tsx` 管理主题状态
    *   后端新增 `/api/v1/scenarios/{id}/timeline` 接口
*   **涉及文件**: `Dashboard.tsx`, `App.tsx`, `theme.ts`, `endpoints.py`

## 5. 核心业务场景 (Core Use Cases)
### 5.1 灵敏度测试 (Sensitivity Search)
*   **实现**: 算法策略。闭环扫描下行功率，通过 BLER 反馈寻找临界点。
### 5.2 阻塞干扰分析 (Blocking Analysis)
*   **实现**: 混合策略。VSG 扫描干扰频点和功率，监测吞吐量损失。
### 5.3 动态衰落场景 (Dynamic Fading)
*   **实现**: 时间轴策略。动态模拟高铁速度变化和场景切换。

---

## 6. 质量保证与 CI/CD 流水线

### 6.1 持续集成架构

项目采用 **GitHub Actions** 作为 CI/CD 平台，在每次代码推送时自动执行质量检查和测试。

#### 工作流程配置

```yaml
# .github/workflows/ci.yml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint → test-backend → test-frontend
```

**分阶段策略**：
1. **Lint 阶段**：快速代码质量检查（1分钟）
2. **测试阶段**：运行单元测试和集成测试（5分钟）
3. **构建阶段**：验证代码可正确编译/打包（2分钟）

### 6.2 代码质量检查工具

#### 后端 - Python Lint

**工具栈**：
- **Ruff** (主 Linter)：基于 Rust 的超快速 Python Linter
- **MyPy** (类型检查)：静态类型分析，可选检查

**Ruff 配置策略** (`.ruff.toml`)：

```toml
[lint]
ignore = [
    "E402",  # Module import not at top
    "E501",  # Line too long - 允许合理的长行
    "E701",  # Multiple statements (colon) - 紧凑代码风格
    "E702",  # Multiple statements (semicolon)
    "E722",  # Bare except - 清理代码允许捕获所有异常
    "F841",  # Unused variable - 占位符变量
]
```

**设计理念 - 务实平衡**：
```
严格检查 ←────[ 我们的位置 ]────→ 宽松检查
│                  ↑                    │
银行/医疗/航天  测试自动化工具    个人原型项目
```

**权衡决策**：
- ✅ **保留**：未使用导入、类型错误、导入排序
- ❌ **忽略**：行长度限制、一行多语句
- 🎯 **目标**：在代码质量与开发速度间找到平衡

#### 前端 - TypeScript/React Lint

**工具栈**：
- **ESLint**：JavaScript/TypeScript 代码质量检查
- **TypeScript Compiler** (`tsc --noEmit`)：严格类型检查

**ESLint 配置**：
```javascript
{
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "react-refresh/only-export-components": "warn"
  }
}
```

### 6.3 CI 运行环境

#### GitHub Actions Runner 规格

```yaml
runs-on: ubuntu-latest
# - CPU: 2核
# - 内存: 7 GB
# - 存储: 14 GB SSD
```

#### 运行成本

**GitHub Actions 免费额度**：
- 公开仓库：✅ **无限制免费**
- 私有仓库：2000 分钟/月

**我们的使用**：
- 单次运行：约 3 分钟
- 每天推送：10 次 × 3 分钟 = 30 分钟
- 每月消耗：约 900 分钟（远低于 2000 分钟限制）

### 6.4 Lint 错误修复记录

**历史遗留问题（2026-01-16 修复）**：

| 工具    | 检测错误数 | 自动修复 | 配置忽略 | 状态 |
|---------|-----------|---------|---------|------|
| ESLint  | 7         | 0       | 7       | ✅   |
| Ruff    | 336       | 243     | 93      | ✅   |
| **总计** | **343**   | **243** | **100** | ✅   |

**修复策略**：
1. **自动修复优先**：使用 `--fix` 修复格式问题
2. **手动修复核心**：修复类型错误、未使用导入
3. **配置忽略合理规则**：对不影响功能的风格问题添加豁免

**典型修复示例**：

```python
# ❌ 修复前：未使用的导入
import tempfile  # Ruff F401 错误

# ✅ 修复后：移除
# (已删除)
```

```typescript
// ❌ 修复前：使用 any 类型
catch (err: any) {
    setError(err.response?.data?.detail);
}

// ✅ 修复后：使用类型断言
catch (err) {
    const detail = (err as {response?: {data?: {detail?: string}}})?.response?.data?.detail;
    setError(detail || '错误');
}
```

### 6.5 最佳实践

#### 本地开发工作流

```bash
# 1. 编写代码
vim backend/drivers/new_feature.py

# 2. 本地检查（推送前）
ruff check backend/
npm run lint

# 3. 自动修复格式问题
ruff check backend/ --fix
npm run lint -- --fix

# 4. 推送代码
git push

# 5. 等待 CI 验证
# GitHub Actions 自动运行检查
```

#### 团队协作规范

1. **PR 必须通过 CI**：所有 Pull Request 必须通过 Lint 和测试
2. **本地先检查**：推送前在本地运行 Lint
3. **配置变更需讨论**：修改 `.ruff.toml` 需团队同意
4. **定期审查规则**：每季度评估规则严格程度

---

## 7. 总结与未来规划

本系统通过严格的质量保证体系和自动化 CI/CD 流水线，确保代码质量的同时保持高效的开发节奏。

**核心设计原则**：
1. **分层架构**：清晰的职责分离，便于维护和扩展
2. **模拟优先**：支持全链路模拟模式，脱离硬件开发
3. **自动化质量保证**：GitHub Actions + Lint 工具确保代码规范
4. **务实平衡**：在严格检查与开发速度间找到最优平衡点

**未来规划**：
- 增加单元测试覆盖率（目标 80%）
- 集成代码覆盖率报告（Codecov）
- 添加性能回归测试
- 探索容器化部署（Docker）
