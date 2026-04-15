#!/usr/bin/env bash
# =============================================================================
#  🦊 APIhdy V5 Supreme - Linux 一键安装管理脚本
#  支持系统：Ubuntu 18.04+ / Debian 9+
#  项目地址：https://github.com/ctsunny/APIhdy_linux
# =============================================================================

# ── 颜色定义 ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
WHITE='\033[1;37m'
DIM='\033[2m'
NC='\033[0m'

# ── 常量 ──────────────────────────────────────────────────────────────────────
SCRIPT_VERSION="5.0"
APP_NAME="apihdy"
INSTALL_DIR="/opt/apihdy"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
CONFIG_FILE="${INSTALL_DIR}/config.json"
LOG_FILE="/var/log/apihdy.log"
SHORTCUT="/usr/local/bin/apihdy"
GITHUB_RAW="https://raw.githubusercontent.com/ctsunny/APIhdy_linux/master"

# ── 工具函数 ──────────────────────────────────────────────────────────────────

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}错误：此脚本需要 root 权限！${NC}"
        echo -e "${YELLOW}请使用：sudo bash $0${NC}"
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        echo -e "${RED}错误：无法识别操作系统！${NC}"
        exit 1
    fi
    # shellcheck disable=SC1091  # /etc/os-release 是系统运行时文件，静态分析无法预读
    . /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        echo -e "${YELLOW}警告：当前系统为 ${PRETTY_NAME}${NC}"
        echo -e "${YELLOW}脚本主要针对 Ubuntu/Debian，其他系统可能存在兼容性问题${NC}"
        echo -n "是否继续？[y/N] "
        read -r reply
        [[ $reply =~ ^[Yy]$ ]] || exit 1
    fi
}

# 随机字母数字字符串（/dev/urandom 适合生成管理凭证，如需更高安全性可改用 openssl rand）
gen_str() {
    local len=${1:-8}
    tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c "$len"
}

# 随机端口（10000-65535）
gen_port() {
    shuf -i 10000-65535 -n 1
}

# 检查端口是否空闲
is_port_free() {
    ! ss -tlnp 2>/dev/null | grep -q ":${1} "
}

# 获取服务器公网 IP
get_ip() {
    local ip
    ip=$(curl -s --max-time 5 https://api.ipify.org 2>/dev/null) \
        || ip=$(curl -s --max-time 5 https://ifconfig.me 2>/dev/null) \
        || ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    echo "${ip:-127.0.0.1}"
}

# 检查是否已安装
is_installed() {
    [[ -f "${CONFIG_FILE}" && -f "${INSTALL_DIR}/server.py" ]]
}

# 用 Python3 读取 config.json 字段（避免依赖 jq）
cfg_get() {
    python3 -c "import json,sys; print(json.load(open('${CONFIG_FILE}'))['$1'])" 2>/dev/null || echo ""
}

# 用 Python3 修改 config.json 字段
cfg_set() {
    python3 - "$1" "$2" << 'PYEOF'
import json, sys
key, val = sys.argv[1], sys.argv[2]
path = "/opt/apihdy/config.json"
with open(path) as f:
    c = json.load(f)
# 尝试转为整数（针对 port 字段）
try:
    c[key] = int(val)
except ValueError:
    c[key] = val
with open(path, 'w') as f:
    json.dump(c, f, ensure_ascii=False, indent=4)
PYEOF
}

# 服务状态文字
svc_status_text() {
    if systemctl is-active --quiet "${APP_NAME}" 2>/dev/null; then
        echo -e "${GREEN}运行中 ✔${NC}"
    else
        echo -e "${RED}已停止 ✘${NC}"
    fi
}

# ── Banner ────────────────────────────────────────────────────────────────────

show_banner() {
    clear
    echo -e "${CYAN}"
    echo "  ╔══════════════════════════════════════════════════════╗"
    echo "  ║    🦊  狐蒂云秒杀系统 V${SCRIPT_VERSION}  ·  Linux 管理面板     ║"
    echo "  ╚══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ── 主菜单 ────────────────────────────────────────────────────────────────────

show_menu() {
    show_banner

    if is_installed; then
        local ip port username panel_path
        ip=$(get_ip)
        port=$(cfg_get port)
        username=$(cfg_get username)
        panel_path=$(cfg_get panel_path)

        echo -e "  ${DIM}服务状态：${NC}$(svc_status_text)"
        echo -e "  ${DIM}访问地址：${NC}${CYAN}http://${ip}:${port}${panel_path}${NC}"
        echo -e "  ${DIM}用 户 名：${NC}${WHITE}${username}${NC}"
        echo ""
        echo -e "  ${WHITE}───────── 管理选项 ─────────${NC}"
        echo ""
        echo -e "  ${GREEN}1.${NC}  查看面板信息"
        echo -e "  ${YELLOW}2.${NC}  重置密码"
        echo -e "  ${CYAN}3.${NC}  无损升级（保留全部数据）"
        echo -e "  ${YELLOW}4.${NC}  重新安装（生成新凭证）"
        echo -e "  ${RED}5.${NC}  卸载"
        echo ""
        echo -e "  ${WHITE}6.${NC}  启动服务"
        echo -e "  ${WHITE}7.${NC}  停止服务"
        echo -e "  ${WHITE}8.${NC}  重启服务"
        echo -e "  ${WHITE}9.${NC}  查看运行日志"
    else
        echo -e "  ${DIM}状态：${NC}${RED}未安装${NC}"
        echo ""
        echo -e "  ${WHITE}───────── 操作选项 ─────────${NC}"
        echo ""
        echo -e "  ${GREEN}1.${NC}  安装"
    fi

    echo ""
    echo -e "  ${WHITE}0.${NC}  退出"
    echo ""
    echo -ne "  请输入选项 [0-9]："
}

# ── 安装依赖 ──────────────────────────────────────────────────────────────────

install_deps() {
    echo -e "${CYAN}[*] 更新软件源...${NC}"
    apt-get update -qq 2>/dev/null

    echo -e "${CYAN}[*] 安装基础依赖（python3, curl, wget）...${NC}"
    apt-get install -y -qq python3 curl wget 2>/dev/null

    echo -e "${GREEN}[✔] 依赖安装完成${NC}"
}

# ── 下载程序文件 ──────────────────────────────────────────────────────────────

download_files() {
    echo -e "${CYAN}[*] 从 GitHub 下载程序文件...${NC}"

    mkdir -p "${INSTALL_DIR}/static/assets"

    local files=(
        "server.py"
        "static/index.html"
        "static/assets/index-v5.js"
        "static/assets/index-v5.css"
    )

    for file in "${files[@]}"; do
        echo -e "  ${DIM}↓ ${file}${NC}"
        if ! curl -fsSL "${GITHUB_RAW}/${file}" -o "${INSTALL_DIR}/${file}" 2>/dev/null; then
            echo -e "${RED}  [✘] 下载失败：${file}${NC}"
            echo -e "${YELLOW}  请检查网络连接后重试${NC}"
            return 1
        fi
    done

    chmod +x "${INSTALL_DIR}/server.py"
    echo -e "${GREEN}[✔] 文件下载完成${NC}"
}

# ── 创建配置文件 ──────────────────────────────────────────────────────────────

create_config() {
    local username=$1 password=$2 panel_path=$3 port=$4

    cat > "${CONFIG_FILE}" << EOF
{
    "username": "${username}",
    "password": "${password}",
    "panel_path": "${panel_path}",
    "port": ${port}
}
EOF
    echo -e "${GREEN}[✔] 配置文件已生成${NC}"
}

# ── 创建 Systemd 服务 ─────────────────────────────────────────────────────────

create_service() {
    cat > "${SERVICE_FILE}" << EOF
[Unit]
Description=APIhdy V5 Supreme - 狐蒂云秒杀系统
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/server.py
Restart=always
RestartSec=5
StandardOutput=append:${LOG_FILE}
StandardError=append:${LOG_FILE}

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "${APP_NAME}" --quiet 2>/dev/null
    echo -e "${GREEN}[✔] Systemd 服务已创建并设置开机自启${NC}"
}

# ── 创建 apihdy 快捷命令 ──────────────────────────────────────────────────────

create_shortcut() {
    cat > "${SHORTCUT}" << 'EOF'
#!/usr/bin/env bash
exec bash /opt/apihdy/install.sh "$@"
EOF
    chmod +x "${SHORTCUT}"
    echo -e "${GREEN}[✔] 快捷命令已创建：输入 ${CYAN}apihdy${GREEN} 即可打开管理菜单${NC}"
}

# ── 打印安装信息 ──────────────────────────────────────────────────────────────

print_info() {
    local ip port username password panel_path
    ip=$(get_ip)
    port=$(cfg_get port)
    username=$(cfg_get username)
    password=$(cfg_get password)
    panel_path=$(cfg_get panel_path)

    echo ""
    echo -e "${CYAN}  ╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}  ║              🎉  面板信息                           ║${NC}"
    echo -e "${CYAN}  ╠══════════════════════════════════════════════════════╣${NC}"
    printf "${CYAN}  ║${NC}  %-8s  ${GREEN}%-40s${CYAN}║${NC}\n" "面板地址" "http://${ip}:${port}${panel_path}"
    printf "${CYAN}  ║${NC}  %-8s  ${GREEN}%-40s${CYAN}║${NC}\n" "用 户 名" "${username}"
    printf "${CYAN}  ║${NC}  %-8s  ${GREEN}%-40s${CYAN}║${NC}\n" "密    码" "${password}"
    printf "${CYAN}  ║${NC}  %-8s  ${GREEN}%-40s${CYAN}║${NC}\n" "端    口" "${port}"
    echo -e "${CYAN}  ╠══════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}  ║${NC}  管理命令：输入 ${YELLOW}apihdy${NC} 打开管理菜单               ${CYAN}║${NC}"
    echo -e "${CYAN}  ╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ── 安装 ──────────────────────────────────────────────────────────────────────

do_install() {
    show_banner
    echo -e "${CYAN}>>> 开始安装 APIhdy V5 Supreme...${NC}"
    echo ""

    check_os

    # 生成随机凭证
    local username password panel_path port
    username=$(gen_str 8)
    password=$(gen_str 16)
    panel_path="/$(gen_str 6)"

    # 生成不冲突的随机端口
    port=$(gen_port)
    local retry=0
    while ! is_port_free "$port" && (( retry < 20 )); do
        port=$(gen_port)
        (( retry++ ))
    done

    echo -e "  ${WHITE}随机生成配置：${NC}"
    echo -e "  用户名：${CYAN}${username}${NC}"
    echo -e "  密  码：${CYAN}${password}${NC}"
    echo -e "  路  径：${CYAN}${panel_path}${NC}"
    echo -e "  端  口：${CYAN}${port}${NC}"
    echo ""

    install_deps
    download_files

    # 将脚本自身复制到安装目录，使 apihdy 命令能自我更新
    cp "$(realpath "$0")" "${INSTALL_DIR}/install.sh" 2>/dev/null || true
    chmod +x "${INSTALL_DIR}/install.sh" 2>/dev/null || true

    create_config "$username" "$password" "$panel_path" "$port"
    create_service
    create_shortcut

    echo -e "${CYAN}[*] 正在启动后台服务...${NC}"
    systemctl start "${APP_NAME}"
    sleep 2

    if systemctl is-active --quiet "${APP_NAME}"; then
        echo -e "${GREEN}[✔] 服务已在后台成功启动${NC}"
    else
        echo -e "${RED}[✘] 服务启动失败，请查看日志：${NC}"
        echo -e "    journalctl -u apihdy -n 30 --no-pager"
    fi

    print_info
}

# ── 卸载 ──────────────────────────────────────────────────────────────────────

do_uninstall() {
    show_banner
    echo -e "${RED}>>> 卸载 APIhdy V5...${NC}"
    echo ""
    echo -ne "  ${YELLOW}确认卸载？所有数据将被删除！[y/N]：${NC}"
    read -r reply
    [[ $reply =~ ^[Yy]$ ]] || { echo "已取消"; return; }

    systemctl stop "${APP_NAME}" 2>/dev/null || true
    systemctl disable "${APP_NAME}" 2>/dev/null || true
    rm -f "${SERVICE_FILE}"
    systemctl daemon-reload
    rm -rf "${INSTALL_DIR}"
    rm -f "${SHORTCUT}"

    echo -e "${GREEN}[✔] 卸载完成${NC}"
}

# ── 无损升级 ──────────────────────────────────────────────────────────────────

do_upgrade() {
    show_banner
    echo -e "${CYAN}>>> 无损升级（保留全部配置与数据）...${NC}"
    echo ""

    # 备份当前配置
    local config_backup
    config_backup=$(cat "${CONFIG_FILE}")
    echo -e "${GREEN}[✔] 已备份当前配置${NC}"

    systemctl stop "${APP_NAME}" 2>/dev/null || true

    download_files

    # 恢复配置（覆写下载可能带来的新 config）
    echo "$config_backup" > "${CONFIG_FILE}"
    echo -e "${GREEN}[✔] 配置已恢复${NC}"

    # 同步最新安装脚本到安装目录
    cp "$(realpath "$0")" "${INSTALL_DIR}/install.sh" 2>/dev/null || true
    chmod +x "${INSTALL_DIR}/install.sh" 2>/dev/null || true

    systemctl daemon-reload
    systemctl start "${APP_NAME}"
    sleep 2

    if systemctl is-active --quiet "${APP_NAME}"; then
        echo -e "${GREEN}[✔] 升级成功，服务已恢复运行${NC}"
    else
        echo -e "${RED}[✘] 服务启动失败，请查看日志${NC}"
    fi

    print_info
}

# ── 重置密码 ──────────────────────────────────────────────────────────────────

do_reset_password() {
    show_banner
    echo -e "${CYAN}>>> 重置登录密码...${NC}"
    echo ""

    local new_password
    new_password=$(gen_str 16)

    cfg_set password "$new_password"

    systemctl restart "${APP_NAME}"

    local ip port panel_path username
    ip=$(get_ip)
    port=$(cfg_get port)
    panel_path=$(cfg_get panel_path)
    username=$(cfg_get username)

    echo ""
    echo -e "${GREEN}[✔] 密码已重置，新凭证如下：${NC}"
    echo ""
    echo -e "${CYAN}  ╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}  ║                🔑  新登录信息                       ║${NC}"
    echo -e "${CYAN}  ╠══════════════════════════════════════════════════════╣${NC}"
    printf "${CYAN}  ║${NC}  %-8s  ${GREEN}%-40s${CYAN}║${NC}\n" "面板地址" "http://${ip}:${port}${panel_path}"
    printf "${CYAN}  ║${NC}  %-8s  ${GREEN}%-40s${CYAN}║${NC}\n" "用 户 名" "${username}"
    printf "${CYAN}  ║${NC}  %-8s  ${GREEN}%-40s${CYAN}║${NC}\n" "新 密 码" "${new_password}"
    echo -e "${CYAN}  ╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ── 重新安装 ──────────────────────────────────────────────────────────────────

do_reinstall() {
    show_banner
    echo -e "${YELLOW}>>> 重新安装（将生成全新随机凭证）...${NC}"
    echo ""
    echo -ne "  ${YELLOW}确认重新安装？当前配置将被覆盖！[y/N]：${NC}"
    read -r reply
    [[ $reply =~ ^[Yy]$ ]] || { echo "已取消"; return; }

    systemctl stop "${APP_NAME}" 2>/dev/null || true
    rm -f "${CONFIG_FILE}" "${INSTALL_DIR}/server.py"

    do_install
}

# ── 服务控制 ──────────────────────────────────────────────────────────────────

do_service() {
    case $1 in
        start)
            systemctl start "${APP_NAME}"
            echo -e "${GREEN}[✔] 服务已启动${NC}"
            ;;
        stop)
            systemctl stop "${APP_NAME}"
            echo -e "${YELLOW}[*] 服务已停止${NC}"
            ;;
        restart)
            systemctl restart "${APP_NAME}"
            echo -e "${GREEN}[✔] 服务已重启${NC}"
            ;;
    esac
}

# ── 查看日志 ──────────────────────────────────────────────────────────────────

show_logs() {
    echo -e "${CYAN}=== 实时日志（Ctrl+C 退出）===${NC}"
    echo ""
    if [[ -f "${LOG_FILE}" ]]; then
        tail -f "${LOG_FILE}"
    else
        journalctl -u "${APP_NAME}" -f --no-pager
    fi
}

# ── 主入口 ────────────────────────────────────────────────────────────────────

main() {
    check_root

    while true; do
        show_menu
        read -r choice
        echo ""

        if is_installed; then
            case "$choice" in
                1) print_info; echo -e "  服务状态：$(svc_status_text)" ;;
                2) do_reset_password ;;
                3) do_upgrade ;;
                4) do_reinstall ;;
                5) do_uninstall ;;
                6) do_service start ;;
                7) do_service stop ;;
                8) do_service restart ;;
                9) show_logs ;;
                0) echo -e "${GREEN}再见！${NC}"; exit 0 ;;
                *) echo -e "${RED}  无效选项，请重新输入${NC}" ;;
            esac
        else
            case "$choice" in
                1) do_install ;;
                0) echo -e "${GREEN}再见！${NC}"; exit 0 ;;
                *) echo -e "${RED}  无效选项，请重新输入${NC}" ;;
            esac
        fi

        echo ""
        echo -ne "  按 ${DIM}Enter${NC} 键返回主菜单..."
        read -r
    done
}

main "$@"
