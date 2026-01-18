# TCU 设备集成文档

## 简介

TCU（Test Config Unit）是测试配置单元，用于通过SCPI指令控制系统中的射频开关、探头、放大器、功分器、双工器等RF器件。本文档说明如何在终端宽带标准信道验证系统中使用TCU。

## 架构位置

```
系统架构层次
├── Sequencer (测试序列器)
│   └── 编排测试流程，调用各仪表
├── HAL (硬件抽象层)
│   ├── VNA
│   ├── VSG
│   ├── Channel Emulator
│   ├── Integrated Tester
│   ├── Spectrum Analyzer
│   └── TCU ← 新增
└── Drivers (驱动层)
    ├── GenericTCU (通用驱动基类)
    └── EMCenter_Driver (EMCenter专用驱动)
```

TCU与其他仪表（VNA、VSG等）平级，通过统一的HAL接口被Sequencer调用。

## 配置文件

### 在 `backend/config.yaml` 中配置 TCU

```yaml
instruments:
  # ... 其他仪表配置 ...
  
  tcu:
    address: "TCPIP0::192.168.1.105::inst0::INSTR"  # VISA地址
    timeout: 3000  # 超时时间（毫秒）
    reset: false   # 连接时不自动复位（TCU通常保持状态）
```

**参数说明**：
- `address`: TCU的VISA资源地址（TCP/IP或USB）
- `timeout`: 通信超时时间，单位毫秒
- `reset`: 是否在连接时执行`*RST`复位，TCU一般设为`false`

## 场景文件使用

TCU可在场景文件的timeline中通过事件驱动方式控制。

### 示例：TCU演示场景

创建文件 `backend/scenarios/tcu_demo.yaml`：

```yaml
metadata:
  id: "TCU_DEMO"
  name: "TCU设备功能演示"
  version: "1.0"
  author: "System"

config:
  type: "dynamic_scenario"
  total_duration: 20  # 总时长20秒
  
  # 时间轴事件
  timeline:
    # T+0: 切换射频通路
    - time: 0
      target: "tcu"
      action: "switch_rf_path"
      params: { path: "ANT1_TO_DUT" }
      comment: "连接天线1到DUT"
    
    # T+3: 设置衰减器
    - time: 3
      target: "tcu"
      action: "set_attenuation"
      params: { port: "ATT1", db: 10.0 }
      comment: "设置ATT1衰减10dB"
    
    # T+6: 开启放大器
    - time: 6
      target: "tcu"
      action: "enable_amplifier"
      params: { port: "AMP1", enable: true }
      comment: "开启AMP1放大器"
    
    # T+12: 调整衰减
    - time: 12
      target: "tcu"
      action: "set_attenuation"
      params: { port: "ATT1", db: 20.0 }
      comment: "增加衰减至20dB"
    
    # T+15: 关闭放大器
    - time: 15
      target: "tcu"
      action: "enable_amplifier"
      params: { port: "AMP1", enable: false }
      comment: "关闭AMP1放大器"
    
    # T+18: 切换到备用通路
    - time: 18
      target: "tcu"
      action: "switch_rf_path"
      params: { path: "ANT2_TO_DUT" }
      comment: "切换到天线2"

  # 数据采样配置
  metrics:
    interval: 0.5
```

### 复杂应用：与信道模拟器配合

在高铁场景中，使用TCU动态切换天线以模拟小区切换：

```yaml
timeline:
  - time: 0
    target: "channel_emulator"
    action: "load_channel_model"
    params: { model: "HST_Cell1.scn" }
  
  - time: 0
    target: "tcu"
    action: "switch_rf_path"
    params: { path: "CE_CELL1_TO_DUT" }
    comment: "连接小区1"
  
  # ... 列车运行 ...
  
  - time: 30
    target: "tcu"
    action: "switch_rf_path"
    params: { path: "CE_CELL2_TO_DUT" }
    comment: "切换到小区2（模拟切换）"
```

## TCU驱动接口

### 标准方法

所有TCU驱动（无论厂商）都实现以下标准接口：

| 方法 | 参数 | 说明 |
|------|------|------|
| `switch_rf_path(path)` | `path`: 通路名称（字符串） | 切换RF开关到指定通路 |
| `set_attenuation(port, db)` | `port`: 端口名称<br>`db`: 衰减值（浮点） | 设置衰减器 |
| `enable_amplifier(port, enable)` | `port`: 端口名称<br>`enable`: 布尔值 | 开关放大器 |
| `get_switch_state(path)` | `path`: 通路名称 | 查询开关状态（返回字符串） |

### EMCenter特有方法（待手册确认）

| 方法 | 说明 | 状态 |
|------|------|------|
| `calibrate_path(path)` | 校准指定通路 | 待实现 |
| `set_duplexer_mode(mode)` | 设置双工器模式 | 待实现 |
| `configure_power_divider(port, ratio)` | 配置功分器比例 | 待实现 |

## 运行测试

### 模拟模式（无硬件）

```bash
cd /Users/Simon/Tools/WideBand_Performance/backend
source venv/bin/activate  # 或 .venv
python cli_main.py --simulate --scenario scenarios/tcu_demo.yaml
```

**预期输出**：
```
[HH:MM:SS] 正在初始化仪器连接...
[HH:MM:SS] 正在连接 TCU (TCPIP0::192.168.1.105::inst0::INSTR)...
[HH:MM:SS] [模拟] 已连接到 EMCenter，地址: TCPIP0::192.168.1.105::inst0::INSTR
[HH:MM:SS] ✅ TCU 连接成功
[HH:MM:SS] >>> 开始场景: TCU设备功能演示 (预计耗时 20s) <<<
[HH:MM:SS] 执行事件: [tcu] switch_rf_path {'path': 'ANT1_TO_DUT'} # 连接天线1到DUT
[HH:MM:SS] [模拟] EMCenter 切换RF通路: ANT1_TO_DUT
...
```

### 实际硬件模式

上传EMCenter手册并实现SCPI指令后：

```bash
# 1. 确认config.yaml中TCU地址为实际IP
# 2. 运行（不带--simulate）
python cli_main.py --scenario scenarios/tcu_demo.yaml
```

## 待实现功能清单

> [!WARNING]
> **需要EMCenter SCPI手册**
> 
> 以下SCPI指令需要根据手册实现，当前为占位符：

### `generic_tcu.py` 待完善
- [ ] `switch_rf_path()` - 实际SCPI指令（如 `ROUT:CLOSE '<path>'`）
- [ ] `set_attenuation()` - 实际SCPI指令（如 `ATT:<port> <db>`）
- [ ] `enable_amplifier()` - 实际SCPI指令（如 `AMP:<port>:STAT ON|OFF`）
- [ ] `get_switch_state()` - 实际SCPI查询指令（如 `ROUT:PATH:STAT? '<path>'`）

### `emcenter.py` 待完善
- [ ] 所有方法的EMCenter特定SCPI实现
- [ ] 确认`calibrate_path()`等特有功能是否存在
- [ ] 添加手册页码引用（遵循开发铁律）

## 开发原则

根据 GEMINI.md **硬件驱动开发铁律**：

1. **先查后写**：在编写SCPI代码前，必须先查阅 `backend/manual_library` 中的手册
2. **提取证据**：使用 `extract_pdf_info.py` 工具提取指令语法
3. **引用来源**：在代码注释中引用手册及页码（例如：`Ref: EMCenter Manual, p.123`）
4. **拒绝猜测**：严禁凭空猜测指令，不确定时保留TODO标记

### 实施流程

```bash
# 1. 上传手册到 manual_library
cp EMCenter_Manual.pdf backend/manual_library/

# 2. 提取关键信息
cd backend/manual_library
python extract_pdf_info.py EMCenter_Manual.pdf "switch" "attenuation" "amplifier"

# 3. 根据提取结果修改 emcenter.py，添加实际SCPI指令
# 4. 在代码中添加手册引用注释

# 5. 测试（先模拟，后实机）
cd ..
python cli_main.py --simulate --scenario scenarios/tcu_demo.yaml
```

## 故障排查

### TCU连接失败

**症状**：`❌ TCU 连接失败: [Errno XXX]`

**排查步骤**：
1. 检查网络连通性：`ping 192.168.1.105`
2. 确认VISA地址格式正确
3. 检查TCU是否开机且网络配置正确
4. 尝试使用NI MAX或Keysight Connection Expert测试连接

### 场景执行时找不到TCU

**症状**：`未找到目标仪表: tcu`

**原因**：`config.yaml`中未配置`tcu`或Sequencer未正确加载

**解决**：
1. 确认`config.yaml`包含`tcu`配置项
2. 检查`sequencer.py`的`factory_map`包含`'tcu': (TCU, "TCU")`

### 模拟模式下方法未响应

**症状**：日志显示警告 `xxx() 尚未实现`

**说明**：这是正常现象，方法占位符在模拟模式下仅记录日志。实机模式需要实现SCPI指令。

## 下一步

1. **等待用户上传EMCenter SCPI手册**
2. 使用`extract_pdf_info.py`提取指令
3. 在`emcenter.py`中实现具体SCPI指令
4. 使用实际硬件验证功能
5. 扩展更多TCU高级功能（如路径校准、状态查询等）
