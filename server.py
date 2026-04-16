#!/usr/bin/env python3
# APIhdy V5 Supreme - Linux 原生服务器
# 狐蒂云极速秒杀系统 - Linux 版
# 依赖：Python 3.6+ 标准库（无需额外安装）

import base64
import binascii
import datetime
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH  = os.path.join(BASE_DIR, 'config.json')
SETTINGS_PATH = os.path.join(BASE_DIR, 'settings.json')


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

# ── 默认设置 ──────────────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    'site_remark': '',
    'notify': {
        'telegram': {'enabled': False, 'bot_token': '', 'chat_id': ''},
        'qmsg':     {'enabled': False, 'token': '', 'qq': ''},
        'bark':     {'enabled': False, 'key': '', 'server': 'https://api.day.app'},
    },
    'notify_events': {
        'start': True, 'stop': True, 'success': True, 'error': True, 'timeout': True,
    },
}


def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return {k: v for k, v in DEFAULT_SETTINGS.items()}
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        # Deep-merge with defaults so new keys are always present
        merged = {k: v for k, v in DEFAULT_SETTINGS.items()}
        merged.update(saved)
        # Ensure sub-dicts exist
        for sub in ('notify', 'notify_events'):
            if not isinstance(merged.get(sub), dict):
                merged[sub] = DEFAULT_SETTINGS[sub]
        for ch in ('telegram', 'qmsg', 'bark'):
            if not isinstance(merged['notify'].get(ch), dict):
                merged['notify'][ch] = DEFAULT_SETTINGS['notify'][ch]
        return merged
    except Exception:
        return {k: v for k, v in DEFAULT_SETTINGS.items()}


def save_settings(data):
    with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ── 通知 ──────────────────────────────────────────────────────────────────────

def _now_str():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _send_telegram(cfg, msg):
    token   = cfg.get('bot_token', '').strip()
    chat_id = cfg.get('chat_id', '').strip()
    if not token or not chat_id:
        return
    try:
        url  = f'https://api.telegram.org/bot{token}/sendMessage'
        body = json.dumps({'chat_id': chat_id, 'text': msg}).encode('utf-8')
        req  = urllib.request.Request(
            url, data=body, method='POST',
            headers={'Content-Type': 'application/json'},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f'[Notify][TG] {e}', flush=True)


def _send_qmsg(cfg, msg):
    token = cfg.get('token', '').strip()
    if not token:
        return
    try:
        qq     = cfg.get('qq', '').strip()
        params = 'msg=' + urllib.parse.quote(msg)
        if qq:
            params += '&qq=' + urllib.parse.quote(qq)
        req = urllib.request.Request(
            f'https://qmsg.zendee.cn/send/{token}',
            data=params.encode('utf-8'), method='POST',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f'[Notify][Qmsg] {e}', flush=True)


def _send_bark(cfg, msg, title='APIhdy通知'):
    key    = cfg.get('key', '').strip()
    server = cfg.get('server', 'https://api.day.app').rstrip('/')
    if not key:
        return
    try:
        url = (f'{server}/{urllib.parse.quote(key, safe="")}'
               f'/{urllib.parse.quote(title, safe="")}'
               f'/{urllib.parse.quote(msg, safe="")}')
        urllib.request.urlopen(urllib.request.Request(url, method='GET'), timeout=10)
    except Exception as e:
        print(f'[Notify][Bark] {e}', flush=True)


def send_notification(event, task_info, extra=None):
    """非阻塞发送通知到已启用的渠道。"""
    settings = load_settings()
    if not settings.get('notify_events', {}).get(event, True):
        return

    site_remark = settings.get('site_remark', '').strip() or '服务器'
    task_id     = task_info.get('id', 'N/A')
    count       = task_info.get('count', 0)

    icons = {'start': '🚀', 'stop': '⏹', 'success': '✅', 'error': '❌', 'timeout': '⏰'}
    names = {
        'start': '任务启动', 'stop': '任务停止',
        'success': '购买成功', 'error': '任务出错', 'timeout': '任务超时',
    }

    lines = [
        f'{icons.get(event, "📢")} 【{site_remark}】{names.get(event, event)}',
        f'📋 任务ID: {task_id}',
        f'⏰ 时间: {_now_str()}',
    ]
    if count > 0:
        lines.append(f'✅ 累计成功: {count} 次')
    if extra:
        if extra.get('order_id'):
            lines.append(f'🔖 单号: {extra["order_id"]}')
        if extra.get('msg'):
            lines.append(f'💬 信息: {extra["msg"]}')

    msg        = '\n'.join(lines)
    notify_cfg = settings.get('notify', {})

    for fn, ch_cfg in [
        (_send_telegram, notify_cfg.get('telegram', {})),
        (_send_qmsg,     notify_cfg.get('qmsg', {})),
        (_send_bark,     notify_cfg.get('bark', {})),
    ]:
        if ch_cfg.get('enabled'):
            threading.Thread(target=fn, args=(ch_cfg, msg), daemon=True).start()


# ── 任务管理器 ────────────────────────────────────────────────────────────────

class TaskManager:
    """在后台线程中运行持久购买任务，即使浏览器关闭也继续执行。"""

    def __init__(self):
        self._tasks: dict = {}
        self._lock  = threading.Lock()

    # ── 公共 API ──────────────────────────────────────────────────────────────

    def start(self, task_cfg: dict) -> str:
        task_id = uuid.uuid4().hex[:8]
        task = {
            'id':         task_id,
            'status':     'running',
            'count':      0,
            'start_time': _now_str(),
            'last_order': None,
            'logs':       [],
            '_stop':      False,
            '_cfg':       task_cfg,
        }
        with self._lock:
            self._tasks[task_id] = task
        threading.Thread(target=self._run, args=(task_id,), daemon=True).start()
        print(f'[TaskMgr] 任务 {task_id} 已启动', flush=True)
        return task_id

    def stop(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return False
        task['_stop'] = True
        return True

    def stop_all(self):
        with self._lock:
            ids = list(self._tasks.keys())
        for tid in ids:
            self.stop(tid)

    def list_tasks(self) -> list:
        with self._lock:
            tasks = list(self._tasks.values())
        return [self._public(t) for t in tasks]

    def get_task(self, task_id: str):
        with self._lock:
            t = self._tasks.get(task_id)
        return self._public(t) if t else None

    # ── 内部 ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _public(task: dict) -> dict:
        return {k: v for k, v in task.items() if not k.startswith('_')}

    def _log(self, task: dict, msg: str):
        entry = f'[{datetime.datetime.now().strftime("%H:%M:%S")}] {msg}'
        task['logs'].append(entry)
        task['logs'] = task['logs'][-100:]
        print(f'[Task {task["id"]}] {msg}', flush=True)

    def _run(self, task_id: str):
        with self._lock:
            task = self._tasks[task_id]
        cfg = task['_cfg']

        url        = cfg.get('url', '').strip()
        method     = cfg.get('method', 'POST').upper()
        headers    = dict(cfg.get('headers', {}))
        body       = cfg.get('body', '')
        interval   = max(0.2, float(cfg.get('interval', 1.0)))
        max_count  = int(cfg.get('max_count', 0))   # 0 = 不限
        timeout_s  = int(cfg.get('timeout', 0))     # 0 = 不限
        do_loop    = bool(cfg.get('loop', True))

        if not url:
            self._log(task, '❌ 任务 URL 为空，无法启动')
            task['status'] = 'error'
            return

        send_notification('start', task)
        start_ts = time.time()

        while not task['_stop']:
            # 超时检查
            if timeout_s and (time.time() - start_ts) > timeout_s:
                task['status'] = 'timeout'
                self._log(task, '⏰ 任务已超时')
                send_notification('timeout', task)
                return

            # 最大次数检查
            if max_count and task['count'] >= max_count:
                task['status'] = 'stopped'
                self._log(task, f'✅ 已达最大次数 {max_count}，停止')
                send_notification('stop', task)
                return

            try:
                body_bytes = body.encode('utf-8') if isinstance(body, str) else (body or b'')
                req = urllib.request.Request(
                    url=url,
                    data=body_bytes if method != 'GET' else None,
                    method=method,
                    headers=headers,
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_json = json.loads(resp.read())

                status = resp_json.get('status')
                if status in (200, '200'):
                    order_id = (resp_json.get('data') or {}).get('invoiceid', '')
                    task['count'] += 1
                    task['last_order'] = order_id
                    self._log(task, f'✅ 成功 #{task["count"]}  单号:{order_id or "N/A"}')
                    send_notification('success', task, {'order_id': order_id})
                    if not do_loop:
                        task['status'] = 'success'
                        return
                else:
                    err = resp_json.get('msg', str(status))
                    self._log(task, f'❌ 失败: {err}')

            except urllib.error.HTTPError as e:
                self._log(task, f'HTTP {e.code}: {e.reason}')
                if e.code in (401, 403):
                    task['status'] = 'error'
                    send_notification('error', task, {'msg': f'认证失败 HTTP {e.code}'})
                    return

            except Exception as e:
                self._log(task, f'❌ 错误: {e}')
                task['status'] = 'error'
                send_notification('error', task, {'msg': str(e)})
                return

            time.sleep(interval)

        task['status'] = 'stopped'
        send_notification('stop', task)


task_mgr = TaskManager()


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
        except (binascii.Error, UnicodeDecodeError):
            # 无效的 Base64 编码或非 UTF-8 字符视为认证失败
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

        # API 端点（需要 Basic Auth）
        api_paths = {'/api/settings', '/api/task/status'}
        if PANEL_PATH:
            api_paths.update({f'{PANEL_PATH}/api/settings', f'{PANEL_PATH}/api/task/status'})
        if raw_path in api_paths:
            if not self._check_basic_auth():
                self._request_auth()
                return
            self._handle_api_get(raw_path)
            return

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

        # 根路径处理：
        # 1. 未设置面板路径时的直接访问（开发/无路径保护模式）
        # 2. 设置了面板路径时，前端 index.html 中的 history.replaceState('/') 会将
        #    浏览器 URL 从面板路径改为 '/'，此处确保刷新页面时仍能正常加载应用。
        #    两种情况均需通过 Basic Auth 认证，安全策略不变。
        if raw_path == '/' or raw_path == '':
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

        # API 端点（需要 Basic Auth）
        api_post_paths = {'/api/settings', '/api/task/start', '/api/task/stop'}
        if PANEL_PATH:
            api_post_paths.update({
                f'{PANEL_PATH}/api/settings',
                f'{PANEL_PATH}/api/task/start',
                f'{PANEL_PATH}/api/task/stop',
            })

        if raw_path in proxy_paths:
            self._proxy_login()
        elif raw_path in api_post_paths:
            if not self._check_basic_auth():
                self._request_auth()
                return
            self._handle_api_post(raw_path)
        else:
            self.send_error(404, 'Not Found')

    # ── JSON 响应辅助 ────────────────────────────────────────────────────────

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── API GET ───────────────────────────────────────────────────────────────

    def _handle_api_get(self, raw_path):
        endpoint = raw_path.split('/')[-1]          # 'settings' 或 'status'
        if endpoint == 'settings':
            self._send_json({'code': 1, 'data': load_settings()})
        elif endpoint == 'status':
            # ?id=<task_id> 返回单个任务；否则返回全部
            qs   = self.path.split('?', 1)[1] if '?' in self.path else ''
            params = dict(urllib.parse.parse_qsl(qs))
            tid  = params.get('id')
            if tid:
                t = task_mgr.get_task(tid)
                if t:
                    self._send_json({'code': 1, 'data': t})
                else:
                    self._send_json({'code': 0, 'msg': '任务不存在'}, 404)
            else:
                self._send_json({'code': 1, 'data': task_mgr.list_tasks()})
        else:
            self.send_error(404, 'Not Found')

    # ── API POST ──────────────────────────────────────────────────────────────

    def _handle_api_post(self, raw_path):
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length) if length > 0 else b'{}'
        try:
            payload = json.loads(body)
        except Exception:
            self._send_json({'code': 0, 'msg': '无效 JSON'}, 400)
            return

        endpoint = raw_path.split('/')[-1]

        if endpoint == 'settings':
            save_settings(payload)
            self._send_json({'code': 1, 'msg': '设置已保存'})

        elif endpoint == 'start':
            if not payload.get('url'):
                self._send_json({'code': 0, 'msg': '缺少 url 参数'}, 400)
                return
            task_id = task_mgr.start(payload)
            self._send_json({'code': 1, 'msg': '任务已启动', 'task_id': task_id})

        elif endpoint == 'stop':
            tid = payload.get('task_id', '')
            if not tid:
                # 停止所有任务
                task_mgr.stop_all()
                self._send_json({'code': 1, 'msg': '所有任务已停止'})
            else:
                ok = task_mgr.stop(tid)
                if ok:
                    self._send_json({'code': 1, 'msg': f'任务 {tid} 已停止'})
                else:
                    self._send_json({'code': 0, 'msg': '任务不存在'}, 404)
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
    # 监听全部网卡，请确保服务器防火墙已限制不必要的 IP 访问（见 README 故障排查）
    print('  服务已启动，按 Ctrl+C 停止\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n[*] 服务已停止')
        httpd.server_close()
