# 🦊 狐蒂云极速秒杀系统 V5.0 · Linux 版

> **APIhdy V5 Supreme** · 一键部署 · 菜单管理 · Ubuntu / Debian

---

## 目录

1. [系统要求](#系统要求)
2. [一键安装](#一键安装)
3. [管理菜单说明](#管理菜单说明)
4. [升级](#升级)
5. [重置密码](#重置密码)
6. [重新安装](#重新安装)
7. [卸载](#卸载)
8. [服务控制](#服务控制)
9. [查看日志](#查看日志)
10. [目录结构](#目录结构)
11. [故障排查](#故障排查)
12. [常见问题 FAQ](#常见问题-faq)
13. [Windows 版本说明](#windows-版本说明)

---

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 18.04 / 20.04 / 22.04 / 24.04、Debian 9 / 10 / 11 / 12 |
| 架构 | x86\_64 / aarch64 |
| 权限 | **root**（必须） |
| 网络 | 需能访问 GitHub（下载程序文件） |
| 依赖 | Python 3.6+（脚本自动安装） |

> 无需手动安装任何依赖，脚本会全自动处理。

---

## 一键安装

### 方法一：推荐（通过 curl）

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ctsunny/APIhdy_linux/master/install.sh)
```

### 方法二：手动下载后运行

```bash
wget -O install.sh https://raw.githubusercontent.com/ctsunny/APIhdy_linux/master/install.sh
chmod +x install.sh
bash install.sh
```

---

### 安装流程说明

运行脚本后会 **优先弹出管理菜单**，不会自动部署。在菜单中选择 **`1. 安装`** 开始部署：

```
  ╔══════════════════════════════════════════════════════╗
  ║    🦊  狐蒂云秒杀系统 V5.0  ·  Linux 管理面板     ║
  ╚══════════════════════════════════════════════════════╝

  状态：未安装

  ───────── 操作选项 ─────────

  1.  安装

  0.  退出

  请输入选项 [0-9]：
```

安装过程会自动：

1. 检测操作系统（仅支持 Ubuntu / Debian，其他系统需手动确认）
2. **随机生成**以下凭证（无需人工填写）：
   - 用户名（8 位字母数字）
   - 密码（16 位高强度随机字符）
   - 面板路径（6 位随机路径，如 `/xk7mAp`）
   - 端口号（10000-65535 随机端口，自动检测冲突）
3. 安装 Python 3 等基础依赖
4. 从 GitHub 下载程序文件
5. 创建并启用 **systemd 后台服务**（开机自启）
6. 打印安装结果信息

---

### 安装完成后的输出示例

```
  ╔══════════════════════════════════════════════════════╗
  ║              🎉  面板信息                           ║
  ╠══════════════════════════════════════════════════════╣
  ║  面板地址  http://1.2.3.4:34521/xk7mAp             ║
  ║  用 户 名  aB3cD4eF                                 ║
  ║  密    码  xQ9mK2pR7wL5nT4v                        ║
  ║  端    口  34521                                    ║
  ╠══════════════════════════════════════════════════════╣
  ║  管理命令：输入 apihdy 打开管理菜单               ║
  ╚══════════════════════════════════════════════════════╝
```

---

### 安装后的快捷管理命令

安装完成后，系统会自动创建 `apihdy` 快捷命令，之后只需运行：

```bash
apihdy
```

即可重新打开完整管理菜单。

---

## 管理菜单说明

安装完成后运行 `apihdy` 将显示完整管理菜单：

```
  状态：运行中 ✔
  访问地址：http://1.2.3.4:34521/xk7mAp
  用 户 名：aB3cD4eF

  ───────── 管理选项 ─────────

  1.  查看面板信息
  2.  重置密码
  3.  无损升级（保留全部数据）
  4.  重新安装（生成新凭证）
  5.  卸载

  6.  启动服务
  7.  停止服务
  8.  重启服务
  9.  查看运行日志

  0.  退出
```

| 选项 | 功能 | 说明 |
|------|------|------|
| 1 | 查看面板信息 | 显示当前面板地址、用户名、密码、端口及服务状态 |
| 2 | 重置密码 | 生成新的随机密码并重启服务 |
| 3 | 无损升级 | 下载最新程序文件，**完全保留现有配置和数据** |
| 4 | 重新安装 | 清除旧文件，生成全新随机凭证后重新安装 |
| 5 | 卸载 | 停止服务并删除所有文件 |
| 6 | 启动服务 | 手动启动后台服务 |
| 7 | 停止服务 | 停止后台服务（不删除配置） |
| 8 | 重启服务 | 重启后台服务（修改配置后需执行） |
| 9 | 查看日志 | 实时跟踪服务运行日志 |

---

## 升级

无损升级会保留 **所有现有配置**（用户名、密码、端口、面板路径），仅更新程序文件。

```bash
apihdy
# 选择 3 - 无损升级
```

或者直接重新下载最新脚本后执行：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ctsunny/APIhdy_linux/master/install.sh)
# 选择 3 - 无损升级
```

**保留数据范围：**

| 数据项 | 是否保留 |
|--------|----------|
| 用户名 | ✅ 保留 |
| 密码 | ✅ 保留 |
| 面板路径 | ✅ 保留 |
| 端口号 | ✅ 保留 |
| 程序文件 | 🔄 更新为最新版本 |

---

## 重置密码

```bash
apihdy
# 选择 2 - 重置密码
```

脚本会生成一个新的 16 位随机密码，并立即重启服务使其生效。重置完成后会打印新的登录信息。

**注意：** 重置密码不会修改用户名、面板路径或端口。

---

## 重新安装

```bash
apihdy
# 选择 4 - 重新安装
```

重新安装会：

1. 停止当前服务
2. 删除旧的程序文件和配置
3. 重新生成全部随机凭证（用户名、密码、路径、端口）
4. 重新部署并启动服务

**注意：** 重新安装后，旧的面板地址和登录信息将全部失效。

---

## 卸载

```bash
apihdy
# 选择 5 - 卸载
```

卸载会删除：

- 后台 systemd 服务（`/etc/systemd/system/apihdy.service`）
- 程序安装目录（`/opt/apihdy/`）
- 快捷命令（`/usr/local/bin/apihdy`）
- 运行日志（`/var/log/apihdy.log`）

> 卸载前会弹出确认提示，输入 `y` 后才会执行。

---

## 服务控制

也可以直接使用 `systemctl` 管理服务：

```bash
# 启动
systemctl start apihdy

# 停止
systemctl stop apihdy

# 重启
systemctl restart apihdy

# 查看状态
systemctl status apihdy

# 设置开机自启
systemctl enable apihdy

# 取消开机自启
systemctl disable apihdy
```

---

## 查看日志

### 通过管理菜单（实时日志）

```bash
apihdy
# 选择 9 - 查看运行日志
# 按 Ctrl+C 退出
```

### 通过 journalctl

```bash
# 查看最近 50 条日志
journalctl -u apihdy -n 50 --no-pager

# 实时跟踪日志
journalctl -u apihdy -f

# 查看今天的所有日志
journalctl -u apihdy --since today
```

### 查看日志文件

```bash
# 日志文件路径
tail -f /var/log/apihdy.log
```

---

## 目录结构

```
/opt/apihdy/               ← 安装目录
├── server.py              ← Python 原生 HTTP 服务器（无外部依赖）
├── install.sh             ← 管理脚本（apihdy 命令的实体）
├── config.json            ← 配置文件（用户名/密码/路径/端口）
└── static/                ← 前端静态文件
    ├── index.html
    └── assets/
        ├── index-v5.js
        └── index-v5.css

/etc/systemd/system/
└── apihdy.service         ← Systemd 服务配置

/usr/local/bin/
└── apihdy                 ← 全局快捷命令

/var/log/
└── apihdy.log             ← 运行日志
```

### 配置文件格式（`/opt/apihdy/config.json`）

```json
{
    "username": "aB3cD4eF",
    "password": "xQ9mK2pR7wL5nT4v",
    "panel_path": "/xk7mAp",
    "port": 34521
}
```

修改此文件后需运行 `systemctl restart apihdy` 使其生效。

---

## 故障排查

### 问题 1：安装时提示"无法访问 GitHub"

**原因：** 服务器无法访问 GitHub 的 raw 内容下载地址。

**解决方案：**

1. 检查服务器网络是否正常：`curl -v https://github.com`
2. 尝试设置 DNS：`echo "nameserver 8.8.8.8" >> /etc/resolv.conf`
3. 如仍无法访问，可手动下载文件后上传至服务器：
   - 将 `server.py` 放至 `/opt/apihdy/`
   - 将 `static/` 目录放至 `/opt/apihdy/static/`
   - 手动创建 `/opt/apihdy/config.json`

---

### 问题 2：服务启动失败

```bash
# 查看详细错误
journalctl -u apihdy -n 50 --no-pager

# 常见原因：
# 1. Python 3 未安装
python3 --version

# 2. 端口已被占用
ss -tlnp | grep :端口号

# 3. 配置文件格式错误
python3 -m json.tool /opt/apihdy/config.json
```

---

### 问题 3：无法访问面板

1. **检查服务是否运行：** `systemctl status apihdy`
2. **检查防火墙：**
   ```bash
   # Ubuntu (ufw)
   ufw allow 端口号/tcp
   ufw status

   # 查看 iptables
   iptables -L -n | grep 端口号
   ```
3. **检查云服务商安全组：** 确保对应端口已在安全组/防火墙规则中放行
4. **确认 URL 正确：** 面板路径区分大小写，请严格按照安装信息中的地址访问

---

### 问题 4：登录提示 401 / 密码错误

浏览器访问面板路径时弹出的 HTTP Basic Auth 对话框，需要输入安装时生成的用户名和密码。

如果忘记密码，通过重置密码功能即可恢复：

```bash
apihdy
# 选择 2 - 重置密码
```

---

### 问题 5：pip3 安装失败（Debian 12 / Ubuntu 24.04）

新版系统启用了 PEP 668，若遇到 `externally-managed-environment` 错误，脚本已自动处理（使用 `--break-system-packages` 参数）。若仍有问题：

```bash
pip3 install --break-system-packages flask
```

---

### 问题 6：`apihdy` 命令提示找不到

```bash
# 重新创建快捷命令
echo '#!/usr/bin/env bash
exec bash /opt/apihdy/install.sh "$@"' > /usr/local/bin/apihdy
chmod +x /usr/local/bin/apihdy
```

---

## 常见问题 FAQ

**Q：面板访问需要用户名密码吗？**  
A：是的。首次访问面板路径时，浏览器会弹出 HTTP Basic Auth 对话框，输入安装时生成的用户名和密码即可进入。

**Q：端口和路径可以修改吗？**  
A：可以。直接编辑 `/opt/apihdy/config.json` 中对应字段，然后执行 `systemctl restart apihdy`。

**Q：开机后服务会自动启动吗？**  
A：是的。安装时已通过 `systemctl enable` 设置开机自启。

**Q：可以同时运行多个实例吗？**  
A：不建议。如需多实例，建议修改服务名称和端口后手动部署第二份。

**Q：数据存储在哪里？**  
A：所有配置存储在 `/opt/apihdy/config.json`，日志存储在 `/var/log/apihdy.log`。

**Q：升级后登录信息是否会变？**  
A：无损升级（选项 3）**不会改变**登录信息，只更新程序文件。重新安装（选项 4）会生成新的随机凭证。

---

## Windows 版本说明

原始 Windows 版本已迁移至 [`windows/`](windows/) 目录，包含：

| 文件 | 说明 |
|------|------|
| `windows/server.ps1` | PowerShell 原生 HTTP 服务器 |
| `windows/启动秒杀系统_V5.bat` | Windows 一键启动脚本 |
| `windows/static/` | 前端静态文件（与 Linux 版共用同一套前端代码） |

### Windows 版本使用方法

1. 进入 `windows/` 目录
2. 双击 `启动秒杀系统_V5.bat`
3. 浏览器会自动打开 `http://127.0.0.1:8080`

---

## 许可证 / License

本项目代码仅供学习交流使用，请遵守相关法律法规。

---

*最后更新：2025 年 · APIhdy V5 Supreme*
