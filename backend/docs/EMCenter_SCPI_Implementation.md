# EMCenter TCU SCPI实现总结

## 手册信息

**文件**: `EMCenter_SCPI_Cmds_and_Errs_RevA_1801188.pdf`  
**页数**: 88页  
**版本**: Rev A

## 核心发现

### 1. EMCenter 是一个插槽式系统

EMCenter是一个机箱系统，可容纳多个EMSwitch卡。每个指令需要指定插槽编号：

```
格式: <slot>:<command>
示例: 4:INT_RELAY_A_1
```

- `<slot>`: 插槽编号 (通常1-8)
- `<command>`: SCPI指令

### 2. 主要指令集

#### 继电器控制

| 指令 | 功能 | 页码 | 示例 |
|------|------|------|------|
| `INT_RELAY_<R>_<N>` | 设置内部继电器A/B到位置0-6 | p.9 | `4:INT_RELAY_A_3` |
| `INT_RELAY_<R>?` | 查询内部继电器A/B当前位置 | p.8 | `4:INT_RELAY_B?` |
| `EXT_RELAY_<R>_<N>` | 设置外部继电器A/B到位置0-6 | p.11 | `4:EXT_RELAY_A_2` |
| `EXT_RELAY_<R>?` | 查询外部继电器A/B当前位置 | p.10 | `4:EXT_RELAY_A?` |

**参数说明**:
- `<R>`: 继电器标识，`A` 或 `B`
- `<N>`: 位置编号
  - `0` = 全部断开（所有端口开路）
  - `1-6` = 连接到对应端口

#### 温度监测

| 指令 | 功能 | 页码 | 示例 |
|------|------|------|------|
| `INT_TEMPERATURE_<R>?` | 查询内部继电器温度（°C） | p.9 | `4:INT_TEMPERATURE_A?` |

#### 远程继电器（可选扩展）

| 指令格式 | 功能 | 页码 |
|----------|------|------|
| `N11RELAY_<N>?` | 查询远程继电器1的开关N位置 | p.12 |
| `N11RELAY_<N>_<pos>` | 设置远程继电器1的开关N到位置pos | p.12 |
| `N12RELAY_<N>?` | 查询远程继电器2的开关N位置 | p.13 |

### 3. 未找到的功能

经过全手册搜索，EMCenter **不直接支持**以下功能：

❌ **程控衰减器（Attenuator）**
  - 搜索关键词: `ATT`, `ATTEN`, `dB` - 仅发现功率计相关的dBm单位
  - 如需衰减控制，需使用外部程控衰减器模块

❌ **放大器（Amplifier）**
  - 搜索关键词: `AMP`, `GAIN`, `AMPLIFIER` - 仅发现"Amplitude Modulation"
  - 如需控制放大器，需通过继电器切换放大器电源或信号通路

❌ **路径校准（Calibration）**
  - EMSwitch主要用于开关控制，不包含RF校准功能

---

## 驱动实现摘要

### 已实现方法

#### 1. `switch_rf_path(path)`

**实现策略**: 使用继电器控制通路

```python
# 示例使用
tcu.switch_rf_path("INT_RELAY_A_1")  # 切换到端口1
tcu.switch_rf_path("EXT_RELAY_B_3")  # 外部继电器B到端口3
```

**实际SCPI**: `4:INT_RELAY_A_1` (假设插槽4)

#### 2. `set_relay_position(relay_type, relay_id, position)`

**EMCenter专用方法** - 精确控制继电器

```python
# 设置继电器
tcu.set_relay_position("INT_RELAY", "A", 2)  # 内部继电器A到位置2
tcu.set_relay_position("EXT_RELAY", "B", 6)  # 外部继电器B到位置6
```

**实际SCPI**: `4:INT_RELAY_A_2`, `4:EXT_RELAY_B_6`

#### 3. `get_relay_position(relay_type, relay_id)`

**查询继电器当前位置**

```python
# 查询
position = tcu.get_relay_position("INT_RELAY", "A")
print(f"继电器A当前位置: {position}")  # 输出: 0-6
```

**实际SCPI**: `4:INT_RELAY_A?`  
**返回**: `1` (数字表示位置)

#### 4. `get_relay_temperature(relay_id)`

**EMCenter特有功能** - 监控继电器温度

```python
# 温度监测
temp_a = tcu.get_relay_temperature("A")
temp_b = tcu.get_relay_temperature("B")
print(f"继电器A温度: {temp_a}°C")
```

**实际SCPI**: `4:INT_TEMPERATURE_A?`  
**返回**: `353.0` (温度值，摄氏度)

#### 5. `set_slot(slot)`

**设置插槽编号**

```python
# 如果EMSwitch卡在插槽3
tcu.set_slot(3)  # 之后所有命令使用 "3:xxx"
```

### 未完全实现方法（需外部设备）

#### `set_attenuation(port, db)` ⚠️

**状态**: 占位符实现，记录警告日志

**原因**: EMCenter SCPI手册中未找到程控衰减器指令

**替代方案**:
1. 使用外部程控衰减器（如Weinschel 8310系列）并单独控制
2. 通过继电器切换固定衰减器（离散值）

#### `enable_amplifier(port, enable)` ⚠️

**状态**: 占位符实现，记录警告日志

**原因**: EMCenter不直接支持放大器控制

**替代方案**:
1. 使用外部程控放大器并单独控制
2. 通过继电器控制放大器电源或旁路通路

---

## 使用示例

### 场景1: 切换天线通路

```yaml
# tcu_antenna_switch.yaml
timeline:
  - time: 0
    target: "tcu"
    action: "set_relay_position"
    params:
      relay_type: "INT_RELAY"
      relay_id: "A"
      position: 1
    comment: "连接天线1"
  
  - time: 10
    target: "tcu"
    action: "get_relay_temperature"
    params: { relay_id: "A" }
    comment: "检查继电器温度"
  
  - time: 15
    target: "tcu"
    action: "set_relay_position"
    params:
      relay_type: "INT_RELAY"
      relay_id: "A"
      position: 2
    comment: "切换到天线2"
```

### 场景2: 模拟故障切换

```python
# 主路径使用内部继电器A
tcu.set_relay_position("INT_RELAY", "A", 3)

# 备用路径使用外部继电器B
tcu.set_relay_position("EXT_RELAY", "B", 5)

# 检查温度，如果过高切换到备用
temp = tcu.get_relay_temperature("A")
if temp > 350.0:
    logger.warning(f"继电器A温度过高: {temp}°C，切换到备用路径")
    tcu.set_relay_position("EXT_RELAY", "B", 3)
```

---

## 配置建议

### 在 `config.yaml` 中指定插槽

虽然驱动默认使用插槽4，但可以通过HAL层传递配置：

```yaml
instruments:
  tcu:
    address: "TCPIP0::192.168.1.105::inst0::INSTR"
    timeout: 3000
    reset: false
    slot: 3  # 指定EMSwitch卡在插槽3（未来可扩展）
```

### 错误代码参考

EMCenter SCPI手册 p.83 列出了开关错误代码：

| 错误码 | 说明 |
|--------|------|
| 201 | 切换到NC失败（内部继电器） |
| 202 | 切换到NO失败（内部继电器） |
| 203 | NC温度错误（内部继电器） |
| 204 | NO温度错误（内部继电器） |
| 205 | 互锁错误（内部继电器） |
| 206 | 开关A错误或错误1-6 |
| 207 | 开关B错误 |
| 208 | 开关错误 |
| 220 | 开关温度NC |
| 221 | 开关温度NO |

---

## 下一步行动

### ✅ 已完成
- EMCenter SCPI指令提取完成
- 继电器控制方法已实现
- 温度监测功能已实现
- 模拟模式测试通过

### 📋 建议改进

1. **扩展HAL层传递插槽参数**
   - 修改`tcu.py`的`__init__`方法，从配置读取`slot`参数
   - 传递给EMCenter_Driver

2. **创建继电器路径映射**
   - 建立友好路径名到继电器位置的映射
   - 例如: `"ANT1_TO_DUT"` → `INT_RELAY_A_1`

3. **集成外部衰减器/放大器**
   - 如果系统包含外部程控衰减器，创建独立驱动
   - 在HAL层统一接口

4. **错误处理增强**
   - 捕获并解析EMCenter错误代码（201-221）
   - 温度过高时自动告警

5. **实机验证**（需要硬件）
   - 连接实际EMCenter设备
   - 验证SCPI指令响应
   - 测试继电器切换延迟

---

## 手册引用总结

所有实现基于以下手册章节：

- **p.3**: 命令索引和目录
- **p.5**: 语法示例和格式说明
- **p.8-9**: 内部继电器命令（INT_RELAY）
- **p.10-11**: 外部继电器命令（EXT_RELAY）
- **p.12**: 远程继电器和SP6T卡命令
- **p.83**: 错误代码列表

**完整引用**: `EMCenter_SCPI_Cmds_and_Errs_RevA_1801188.pdf`
