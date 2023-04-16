import subprocess
import time
import gnuscreen_reader as screen
import pty
import os
import yaml
import re
from manager import socketio

with open('settings.yml', 'r', encoding="utf-8") as fs:
    settings = yaml.load(fs, Loader=yaml.SafeLoader)

master, slave = pty.openpty()
env = dict(os.environ)
env["TERM"] = "vt100"

console = {}


def start_server(server):
    """
    サーバーを起動させる
    """
    global console

    if server == 'proxy':

        # ディレクトリを指定
        dir = settings['server'][server]['directory']
        p = subprocess.Popen(
            f'screen -S {settings["server"][server]["screen-id"]} {settings["server"][server]["command"]}',
            stdin=slave, stdout=slave, stderr=slave, close_fds=True, shell=True, cwd=dir, env=env
        )

        # コンソールを取得する
        console[server] = ''
        for chunk in screen.read(master):

            # 制御コードの処理
            if chunk == b'\x1b[?1h\x1b=\x1b[0m\x1b(B\x1b[1;24r' or chunk == b'\x1b[H\x1b[J\x1b[H\x1b[J':
                continue
            if re.match(rb'\x1b\[31m.*\x1b\[0m', chunk):
                continue

            # 変数に出力を追加
            console[server] += chunk.decode('utf-8')

            # サーバー終了を検知
            if '[screen is terminating]' in chunk.decode('utf-8'):
                with open('manager/status.yml', 'r') as s:
                    status = yaml.load(s, Loader=yaml.SafeLoader)
                status[server] = 'stop'
                socketio.emit('status', {server: 'stop'})
                with open('manager/status.yml', 'w') as f:
                    yaml.dump(status, f, default_flow_style=False)
                break

            # サーバー起動完了を検知しstatusに保存
            if settings["server"][server]["type"] == 'proxy':
                if 'Listening on' in chunk.decode('utf-8'):
                    with open('manager/status.yml', 'r') as s:
                        status = yaml.load(s, Loader=yaml.SafeLoader)
                    status[server] = 'run'
                    socketio.emit('status', {server: 'run'})
                    with open('manager/status.yml', 'w') as f:
                        yaml.dump(status, f, default_flow_style=False)

            else:
                if 'Done' in chunk.decode('utf-8'):
                    with open('manager/status.yml', 'r') as s:
                        status = yaml.load(s, Loader=yaml.SafeLoader)
                    status[server] = 'run'
                    socketio.emit('status', {server: 'run'})
                    with open('manager/status.yml', 'w') as f:
                        yaml.dump(status, f, default_flow_style=False)


def stop_server(server):
    """
    サーバーを停止させる
    """
    if settings['server'][server]['type'] == 'proxy':
        subprocess.run(f"screen -S {settings['server'][server]['screen-id']} -X stuff end\n", shell=True)
    else:
        subprocess.run(f"screen -S {settings['server'][server]['screen-id']} -X stuff stop\n", shell=True)

"""
def restart_server(server):
    """"""
    サーバーを再起動させる（停止->起動）
    """"""
    stop_server(server)
    if server == 'proxy':
        while True:
            with open('manager/status.yml', 'r') as s:
                status = yaml.load(s, Loader=yaml.SafeLoader)
            if status['proxy'] == "stop":
                break
            time.sleep(0.1)
    elif server == 'lobby':
        while True:
            with open('manager/status.yml', 'r') as s:
                status = yaml.load(s, Loader=yaml.SafeLoader)
            if status['lobby'] == "stop":
                break
            time.sleep(0.1)
    elif server == 'main':
        while True:
            with open('manager/status.yml', 'r') as s:
                status = yaml.load(s, Loader=yaml.SafeLoader)
            if status['main'] == "stop":
                break
            time.sleep(0.1)
    start_server(server)
"""


def exe_command(server, command):
    """
    コマンドを実行する
    """
    if server == 'proxy':
        cmd = f"screen -S {settings['server'][server]['screen-id']} -X stuff {command}\n"
        subprocess.Popen(cmd, shell=True)

