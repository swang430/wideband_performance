# 仪表手册库 (Manual Library)

本目录用于集中管理所有硬件仪表的编程手册 (SCPI Reference) 和用户指南。

## 目录结构
*   `catalog.yaml`: 手册索引文件，定义了仪表类型、型号、厂商及下载链接。
*   `scan_local_library.py`: **[新]** 扫描本地文件夹，将手动放入的 PDF/HTML 文件自动注册到 YAML 索引中。
*   `manage_manuals.py`: 用于查询和查找手册信息的辅助脚本。
*   `download_manuals.py`: 批量下载脚本。

## 核心工作流

### 1. 自动下载 (适用于公开手册)
对于大部分可公开下载的手册，运行以下命令即可自动拉取：
```bash
python3 manual_library/download_manuals.py
```

### 2. 手动添加 (适用于受控/失效链接)
部分高端仪表（如 Spirent Vertex, Anritsu MT8000A）的手册需要登录下载或从光盘获取。

1.  **获取文件**: 通过厂商渠道下载 `.pdf` 或 `.html` 文件。
2.  **放入目录**: 将文件拖入 `manual_library/` 下对应的子目录中。
    *   例如: `manual_library/channel_emulator/Spirent_Vertex/My_Manual.pdf`
    *   如果目录不存在，请参考 `catalog.yaml` 中的分类手动创建 (建议格式: `Vendor_Series`)。
3.  **自动注册**: 运行扫描脚本，将新文件添加到索引：
    ```bash
    python3 manual_library/scan_local_library.py
    ```
4.  **验证**: 运行 `python3 manual_library/manage_manuals.py --list` 确认新文件已显示。

### 3. 自动发现新类型/品牌（推荐）

从现在起，`scan_local_library.py` 会自动补齐 **类别、品牌、系列**，不再要求你先手动改 `catalog.yaml`：

1.  **放置目录**：
    ```
    manual_library/<category>/<Vendor>_<Series>/
    ```
    例如：
    ```
    manual_library/integrated_tester/Keysight_UXM/
    ```
2.  **更准确的命名（可选）**：
    - 如果厂商名里有多个单词或容易混淆，建议使用双下划线分隔：
      ```
      Rohde_and_Schwarz__CMW
      ```
    - 或者在该目录下放一个 `meta.yaml`，显式指定 `vendor/series/models`：
      ```yaml
      vendor: Rohde & Schwarz
      series: CMW
      models: [CMW500]
      ```
3.  **执行扫描**：
    ```bash
    python3 manual_library/scan_local_library.py
    ```
4.  **效果**：脚本会自动新增 `catalog.yaml` 中缺失的类别/品牌/系列，并注册本地手册文件。

> 注意：扫描只处理本地文件；如需补充远程链接或官方下载地址，仍需手动编辑 `catalog.yaml`。

## 如何添加新型号
如果您引入了新的仪表型号（例如 TCU 测试配置单元），请编辑 `catalog.yaml`：

```yaml
# 在 catalog.yaml 中添加
tcu:  # 新的一级分类（已添加）
  - vendor: EMCenter
    series: TCU
    models: [TCU-1000, TCU-2000]
    manuals:
      - title: EMCenter TCU SCPI Programming Manual
        type: scpi_reference
        url: unavailable - pending upload
        notes: 待用户上传 EMCenter TCU SCPI 手册
```
然后手动创建文件夹 `manual_library/tcu/EMCenter_TCU/` 并放入手册，最后运行扫描脚本即可。

## 支持的设备类型
当前手册库支持以下设备分类：
- `spectrum_analyzer` - 频谱分析仪
- `signal_generator` - 信号发生器 (VSG)
- `integrated_tester` - 综合测试仪
- `vna` - 网络分析仪
- `channel_emulator` - 信道模拟器
- `tcu` - 测试配置单元 (射频开关/衰减器/放大器控制)
