# TCU (Test Config Unit) 手册目录

本目录存放TCU测试配置单元的相关手册。

## 关于TCU

TCU（Test Config Unit）用于控制射频测试系统中的各类RF器件，包括：
- **射频开关** - 切换信号通路
- **衰减器** - 调整信号强度
- **放大器** - 放大信号
- **功分器** - 分配功率
- **双工器** - TDD/FDD模式切换
- **探头** - 信号探测

## 支持的厂商

### EMCenter
- **系列**: TCU
- **型号**: TCU-1000, TCU-2000
- **手册状态**: 待上传

请将 EMCenter TCU SCPI 手册放入本目录的 `EMCenter_TCU/` 子文件夹中。

### NI (National Instruments)
- **系列**: PXI Switch
- **型号**: PXI-2593, PXI-2585
- **手册**: 可从官网下载

### Keysight
- **系列**: L47xx
- **型号**: L4750A, L4762A
- **手册**: 可从官网下载

## 上传手册步骤

1. **创建厂商文件夹**（如果不存在）
   ```bash
   mkdir -p EMCenter_TCU
   ```

2. **放入手册文件**
   - 将 PDF 或 HTML 文件拖入对应文件夹
   - 推荐命名：`EMCenter_TCU_SCPI_Programming_Manual.pdf`

3. **运行扫描脚本**
   ```bash
   cd /Users/Simon/Tools/WideBand_Performance/backend/manual_library
   python scan_local_library.py
   ```

4. **验证**
   ```bash
   python manage_manuals.py --list tcu
   ```

## 驱动实现参考

上传手册后，请参考以下文件实现SCPI指令：
- 驱动框架：`backend/drivers/emcenter.py`
- 集成文档：`backend/docs/TCU_INTEGRATION.md`

遵循**硬件驱动开发铁律**（GEMINI.md）：
1. 先查后写 - 先查阅手册，再编写代码
2. 提取证据 - 使用 `extract_pdf_info.py` 定位指令
3. 引用来源 - 代码注释中引用手册页码
4. 拒绝猜测 - 不确定时保留 TODO 标记
