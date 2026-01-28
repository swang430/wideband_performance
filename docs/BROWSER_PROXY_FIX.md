# 浏览器自动化代理冲突解决方案

**问题**: Antigravity 浏览器工具无法连接到 Chrome DevTools Protocol  
**原因**: 本地代理（127.0.0.1:7897）拦截了对 localhost 的连接  
**影响**: 无法使用浏览器自动化测试前端  

---

## 问题诊断

### 错误信息
```
failed to connect to browser via CDP
http://127.0.0.1:9222
Unexpected status 400
```

### 根本原因
```
浏览器工具 → 尝试连接 127.0.0.1:9222 (CDP)
             ↓
本地代理 (127.0.0.1:7897) 拦截请求
             ↓
代理不理解 CDP 协议 → 返回 HTTP 400
```

---

## 解决方案

### 方案 1: 配置 Clash 代理规则（推荐）⭐

如果你使用的是 **Clash** 或 **ClashX**：

#### 步骤 1: 打开配置文件

```bash
# Clash 配置文件位置（通常）
# macOS: ~/.config/clash/config.yaml
# 或者在 ClashX 界面: 配置 → 打开配置文件夹
```

#### 步骤 2: 添加规则

在配置文件中找到 `rules:` 部分，在最前面添加：

```yaml
rules:
  # 本地地址直连（必须在最前面！）
  - DOMAIN,localhost,DIRECT
  - DOMAIN-SUFFIX,local,DIRECT
  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
  
  # 其他规则...
  - MATCH,PROXY
```

**关键点**:
- 规则顺序很重要！本地规则必须在最前面
- `127.0.0.0/8` 覆盖所有 127.x.x.x 地址
- `no-resolve` 防止 DNS 查询

#### 步骤 3: 重启 Clash

```bash
# 方法 1: 重启 ClashX 应用
# 方法 2: 在 ClashX 菜单中点击 "重载配置"
```

#### 步骤 4: 验证

运行测试脚本：

```bash
cd /Users/Simon/Tools/WideBand_Performance
source venv/bin/activate
python tests/diagnose_proxy.py
```

应该看到：
```
✅ localhost 在 no_proxy 列表中（会绕过代理）
✅ 127.0.0.1 在 no_proxy 列表中（会绕过代理）
```

---

### 方案 2: 配置 V2Ray 代理规则

如果你使用的是 **V2Ray** 或 **V2RayX**：

#### 步骤 1: 打开配置文件

```bash
# V2Ray 配置文件位置
# macOS: ~/Library/Application Support/V2RayX/config.json
```

#### 步骤 2: 添加路由规则

在 `routing.rules` 中添加：

```json
{
  "routing": {
    "rules": [
      {
        "type": "field",
        "domain": [
          "localhost",
          "domain:local"
        ],
        "outboundTag": "direct"
      },
      {
        "type": "field",
        "ip": [
          "127.0.0.0/8",
          "10.0.0.0/8",
          "172.16.0.0/12",
          "192.168.0.0/16"
        ],
        "outboundTag": "direct"
      }
    ]
  }
}
```

#### 步骤 3: 重启 V2Ray

---

### 方案 3: 临时禁用代理（快速测试）

如果你只是想快速测试浏览器功能：

#### macOS 系统设置

```bash
# 1. 打开系统设置
系统设置 → 网络 → 高级 → 代理

# 2. 勾选 "排除简单主机名"
# 3. 在 "忽略这些主机与域的代理设置" 中添加：
localhost
127.0.0.1
*.local
```

#### 或使用脚本临时禁用

```bash
# 保存当前代理设置
networksetup -getwebproxy "Wi-Fi" > /tmp/proxy_backup.txt

# 禁用代理
networksetup -setwebproxystate "Wi-Fi" off
networksetup -setsecurewebproxystate "Wi-Fi" off

# 测试浏览器...

# 恢复代理
networksetup -setwebproxystate "Wi-Fi" on
networksetup -setsecurewebproxystate "Wi-Fi" on
```

---

## 验证步骤

### 1. 运行诊断工具

```bash
cd /Users/Simon/Tools/WideBand_Performance
source venv/bin/activate
python tests/diagnose_proxy.py
```

### 2. 检查代理日志

打开你的代理应用（Clash/V2Ray），查看日志标签页。

### 3. 测试浏览器工具

在 Antigravity 中请求运行浏览器测试。

**成功标志**：
- ✅ 浏览器工具能成功连接
- ✅ 能看到网页截图
- ✅ 代理日志中没有对 127.0.0.1:9222 的请求

---

## 常见问题

### Q1: 修改配置后仍然失败？

**检查**：
1. 确认代理软件已重启
2. 确认规则在配置文件最前面
3. 运行 `scutil --proxy` 查看系统代理设置

### Q2: 不确定使用哪个代理软件？

```bash
# 检查正在监听 7897 端口的进程
lsof -i :7897 | head -3
```

常见的：
- `ClashX` - Clash 客户端
- `v2ray-core` - V2Ray
- `Surge` - Surge

### Q3: 想完全禁用代理测试？

**不推荐**，因为会影响你访问国外网站。

但如果只是临时测试：

```bash
# 关闭代理应用
# 或在应用菜单中选择 "关闭代理"

# 测试完成后记得重新打开！
```

---

## 成功后的使用

配置完成后，在 Antigravity 中可以：

```
请求：测试前端 Dashboard 页面

浏览器工具会：
1. ✅ 打开 http://localhost:5173
2. ✅ 截图保存
3. ✅ 点击按钮交互
4. ✅ 验证功能
```

---

## 技术细节

### 为什么会有这个问题？

1. **代理软件的工作原理**：
   - 拦截所有 HTTP/HTTPS 请求
   - 根据规则决定直连还是代理

2. **Chrome DevTools Protocol (CDP)**：
   - 使用 HTTP 作为传输协议
   - 但不是标准的 HTTP 流量
   - 代理软件无法正确处理 → 返回 400

3. **解决思路**：
   - 让代理软件识别 localhost
   - 直接连接，不经过代理

### 为什么 macOS 系统例外列表不起作用？

macOS 的系统代理例外列表主要用于：
- Safari
- 系统网络请求

但 Antigravity 的浏览器工具可能：
- 直接读取代理软件的配置
- 绕过系统设置
- 因此需要在代理软件层面配置

---

## 推荐配置

**长期使用**：方案 1（Clash 规则）或方案 2（V2Ray 规则）  
**快速测试**：方案 3（临时禁用）

**最佳实践**：
```yaml
# Clash 配置示例（完整）
rules:
  # 本地网络直连
  - DOMAIN,localhost,DIRECT
  - IP-CIDR,127.0.0.0/8,DIRECT
  - IP-CIDR,10.0.0.0/8,DIRECT
  - IP-CIDR,192.168.0.0/16,DIRECT
  
  # 中国大陆网站直连
  - GEOIP,CN,DIRECT
  
  # 其他走代理
  - MATCH,PROXY
```

---

**创建日期**: 2026-01-17  
**适用版本**: Antigravity (所有版本)  
**相关问题**: CDP 连接、代理冲突、浏览器自动化
