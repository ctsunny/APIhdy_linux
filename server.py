#!/usr/bin/env python3
# APIhdy V5 Supreme - Linux 原生服务器
# 狐蒂云极速秒杀系统 - Linux 版
# 依赖：Python 3.6+ 标准库（无需额外安装）

import base64
import json
import os
import sys
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"[FATAL] 配置文件不存在: {CONFIG_PATH}", file=sys.stderr)
        print("[FATAL] 请先运行安装脚本: bash install.sh", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


config      = load_config()
TARGET_BASE = 'https://www.szhdy.com'
PANEL_PATH  = config.get('panel_path', '').rstrip('/')   # e.g. "/ab1cd2"
PORT        = int(config.get('port', 8080))
USERNAME    = config.get('username', '')
PASSWORD    = config.get('password', '')
STATIC_DIR  = os.path.join(BASE_DIR, 'static')


class APIhdyHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, fmt, *args):
        sys.stdout.write(
            f"[{self.log_date_time_string()}] {self.address_string()} - {fmt % args}\n"
        )
        sys.stdout.flush()

    # ── 认证 ──────────────────────────────────────────────────────────────────

    def _check_basic_auth(self):
        auth = self.headers.get('Authorization', '')
        if not auth.startswith('Basic '):
            return False
        try:
            decoded = base64.b64decode(auth[6:]).decode('utf-8')
            user, _, pwd = decoded.partition(':')
            return user == USERNAME and pwd == PASSWORD
        except Exception:
            return False

    def _request_auth(self):
        body = b'401 Unauthorized - Please login'
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="APIhdy Panel"')
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── 路由 ──────────────────────────────────────────────────────────────────

    def do_GET(self):
        raw_path = self.path.split('?')[0].split('#')[0]

        # 面板入口（需要 Basic Auth 认证）
        if PANEL_PATH and (raw_path == PANEL_PATH or raw_path == PANEL_PATH + '/'):
            if not self._check_basic_auth():
                self._request_auth()
                return
            self.path = '/index.html'
            return super().do_GET()

        # 静态资源（CSS/JS）供已认证前端加载，无需二次认证
        if raw_path.startswith('/assets/') or raw_path == '/favicon.ico':
            return super().do_GET()

        # 无面板路径时，根路径直接服务（开发/无路径保护模式）
        if not PANEL_PATH and (raw_path == '/' or raw_path == ''):
            if not self._check_basic_auth():
                self._request_auth()
                return
            self.path = '/index.html'
            return super().do_GET()

        # 其他所有路径：404（路径安全屏障）
        self.send_error(404, 'Not Found')

    def do_POST(self):
        raw_path = self.path.split('?')[0]

        # 支持带/不带面板路径的代理端点
        proxy_paths = {'/local_proxy_login'}
        if PANEL_PATH:
            proxy_paths.add(f'{PANEL_PATH}/local_proxy_login')

        if raw_path in proxy_paths:
            self._proxy_login()
        else:
            self.send_error(404, 'Not Found')

    # ── 代理登录 ──────────────────────────────────────────────────────────────

    def _proxy_login(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length) if length > 0 else b''

        try:
            req = urllib.request.Request(
                url=f'{TARGET_BASE}/zjmf_api_login',
                data=body,
                method='POST',
                headers={
                    'Content-Type': self.headers.get('Content-Type', 'application/json'),
                    'User-Agent': 'APIhdy/5.0',
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)

        except Exception as e:
            msg = json.dumps({'code': 0, 'status': 502, 'msg': str(e)}).encode('utf-8')
            self.send_response(502)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)


# ── 启动 ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('=' * 52)
    print('   🦊 APIhdy V5 Supreme - Linux 原生服务器')
    print('=' * 52)
    print(f'  监听地址：0.0.0.0:{PORT}')
    print(f'  面板路径：{PANEL_PATH if PANEL_PATH else "/（无路径保护）"}')
    print(f'  静态目录：{STATIC_DIR}')
    print('=' * 52)
    print()

    httpd = HTTPServer(('0.0.0.0', PORT), APIhdyHandler)
    print('  服务已启动，按 Ctrl+C 停止\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n[*] 服务已停止')
        httpd.server_close()
