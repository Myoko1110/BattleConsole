from manager import app, socketio, FileExplorer, ServerJob
from flask import render_template, request, redirect, make_response, send_file

import datetime
from pathlib import Path
import mimetypes
import os
import re
import secrets
import shutil
import sys
import threading
import time

from werkzeug.utils import secure_filename
import pytz
import yaml


error = False

with open('settings.yml', 'r', encoding="utf-8") as fs:
    settings = yaml.load(fs, Loader=yaml.SafeLoader)

if settings['password'] is None or settings['password'] == "":
    print('\033[31m'+'[ConsoleError] Password is empty. Please set a password.'+'\033[0m')
    error = True

if not FileExplorer.FILE_EXPLORER_ROOT.exists():
    print('\033[31m'+'[ConsoleError] Invalid root path in settings.yml.'+'\033[0m')
    error = True

for i in settings['server'].keys():
    if not Path(settings['server'][i]['directory']).exists():
        print('\033[31m' + f'[ConsoleError] Invalid server "{i}" directory in settings.yml.' + '\033[0m')
        error = True
    if settings['server'][i]['type'] not in ['proxy', 'minecraft']:
        print('\033[31m' + f'[ConsoleError] Invalid server "{i}" type in settings.yml.' + '\033[0m')
        error = True

if error:
    sys.exit()

Pass = settings['password']
socketio_status = 'disconnect'


def check_session():
    while True:
        with open('manager/session.yml', 'r') as file:
            data = yaml.safe_load(file)

        # 現在時刻の取得
        now = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S')

        # timestampが現在時刻を超えたら、該当データを削除
        for key in list(data.keys()):
            timestamp = str(datetime.datetime.strptime(data[key]['timestamp'], '%Y-%m-%d %H:%M:%S'))
            if timestamp < now:
                data.pop(key)
                # yamlファイルに書き込み
                with open('manager/session.yml', 'w') as file:
                    yaml.safe_dump(data, file)
        time.sleep(60)


threading.Thread(target=check_session, daemon=True).start()


def check_cookie():
    with open('manager/session.yml', 'r', encoding="utf-8") as f:
        yml = yaml.load(f, Loader=yaml.SafeLoader)
        true_keys = [key for key, value in yml.items() if value]
        for session in true_keys:
            if 'session' in request.cookies and request.cookies.get('session') == session:
                return True
        else:
            return False


def export_console():
    global socketio_status

    # old = {}
    cmd = {}

    while True:
        with open('manager/status.yml', 'r') as s:
            status = yaml.load(s, Loader=yaml.SafeLoader)
        for s in settings['server'].keys():
            if status[s] == 'stop':
                cmd[s] = 'サーバーは起動していません'
            if status[s] == 'loading' or status[s] == 'run':
                cmd[s] = re.sub(r'\x1b\[.*?[@-~]', '', ServerJob.console[s]).replace("> ", "")

        socketio.emit('console', cmd)
        if socketio_status == 'disconnect':
            break
        time.sleep(0.1)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if check_cookie():
            return redirect('/')
        else:
            return render_template('login.html')

    if request.method == 'POST':
        password = request.form['pass']

        if password != Pass:  # パスワードが違うとき
            err = 'パスワードが間違っています'
            return render_template('login.html', error=err)

        else:  # パスワードが合っているとき
            # 乱数作成
            cookie_value = secrets.token_urlsafe(256)
            print(cookie_value)

            # ymlに保存
            with open('manager/session.yml', 'r', encoding="utf-8") as f:
                yml = yaml.load(f, Loader=yaml.SafeLoader)
                yml[cookie_value] = {}
                yml[cookie_value]['connect'] = True
                weeks_ago = datetime.datetime.now(pytz.timezone('Asia/Tokyo')) + datetime.timedelta(weeks=2)
                yml[cookie_value]['timestamp'] = weeks_ago.strftime('%Y-%m-%d %H:%M:%S')
            with open('manager/session.yml', 'w') as f:
                yaml.dump(yml, f, default_flow_style=False)

            # Cookieの設定
            response = make_response(redirect('/'))
            max_age = 60 * 60 * 24 * 14
            response.set_cookie('session', value=cookie_value, max_age=max_age, path='/')

            # dashboardにリダイレクト
            return response


@app.route('/')
def dash():
    if check_cookie():
        # statusを取得
        with open('manager/status.yml', 'r') as s:
            status = yaml.load(s, Loader=yaml.SafeLoader)

        return render_template('dash.html', status=status, server=settings)

    else:
        return redirect('login')


@app.route('/servers', methods=["GET", "POST"])
def servers():
    if check_cookie():
        if request.method == 'GET':
            # statusを取得
            with open('manager/status.yml', 'r') as s:
                status = yaml.load(s, Loader=yaml.SafeLoader)
            socketio.emit('status', {'proxy': status['proxy'], 'lobby': status['lobby'], 'main': status['main']})

            return render_template('servers.html', status=status, server=settings)

        if request.method == 'POST':
            with open('manager/status.yml', 'r') as s:
                status = yaml.load(s, Loader=yaml.SafeLoader)
            server = list(request.form.items())[0][0]
            if status[server] == "stop":

                # サーバーを起動、statusをrunにする
                t = threading.Thread(target=ServerJob.start_server, args=(server,))
                t.start()
                status[server] = "loading"
                socketio.emit('status', {server: 'loading'})

                # 上書き
                with open('manager/status.yml', 'w') as f:
                    yaml.dump(status, f, default_flow_style=False)

            elif status[server] == "run":

                # サーバーを停止、statusをstopにする
                ServerJob.stop_server(server)
                status[server] = "loading"
                socketio.emit('status', {server: 'loading'})

                # 上書き
                with open('manager/status.yml', 'w') as f:
                    yaml.dump(status, f, default_flow_style=False)

        """
        elif 'proxyR' in request.form:

            # サーバーを再起動させる
            t = threading.Thread(target=mcsv.restart_server, args=('proxy',))
            t.start()
            status['proxy'] = "loading"
            socketio.emit('status', {'proxy': 'loading'})

        """

        return redirect('servers')
    else:
        return redirect('login')


@app.route('/cmd')
def console():
    if check_cookie():
        server = request.args.get("s")
        if server == "" or server is None:
            return redirect(f'?s={list(settings["server"].keys())[0]}')

        return render_template('console.html', server=settings)
    else:
        return redirect('login')


@app.route("/file")
def file_explorer():
    """
    ファイルエクスプローラのページ処理
    引数:
      GET ./?p=(フォルダパス)
    """
    if check_cookie():

        if request.args.get("p") == "" or request.args.get("p") is None:
            return redirect('?p=.')

        current_dir = Path(request.args.get("p") or FileExplorer.FILE_EXPLORER_ROOT)

        # 存在しないパスだったら、安全な限り存在する上の階層に移動する
        while not (
                FileExplorer.FILE_EXPLORER_ROOT / current_dir).exists() and FileExplorer.is_safe_path(current_dir):
            current_dir = current_dir / ".."

        # 安全なパスではなかったら、rootパスにリダイレクト
        if not FileExplorer.is_safe_path(current_dir):
            return redirect("?p=.")

        current_dir = FileExplorer.normalize_path(current_dir)

        _args = dict(
            Path=Path,
            root=FileExplorer.FILE_EXPLORER_ROOT,
            cwd=current_dir.as_posix(),
            sorted_iterdir=FileExplorer.sorted_iterdir,
            number=len(FileExplorer.sorted_iterdir(FileExplorer.FILE_EXPLORER_ROOT / current_dir.as_posix()))
        )
        return render_template('file.html', **_args)
    else:
        return redirect('login')


@app.route("/fio", methods=["GET", "POST"])
def file_io():
    """
    ファイルの入出力
    引数:
      GET    ./?p=(ダウンロードするファイルのパス)
      POST   ./?d=(アップロード先のフォルダパス)
    """
    if check_cookie():
        if request.method == "POST":  # upload
            # 引数の確認
            out_dir = request.args.get("d")  # アップロード先ディレクトリパスを指定
            if out_dir is None or out_dir == '':
                return redirect(f'./file?p=.&i=e,アップロード先のパスが指定されていません。')

            # パスの確認
            out_dir = Path(out_dir)
            if not (FileExplorer.FILE_EXPLORER_ROOT / out_dir).exists():
                return redirect(f'./file?p=.&i=e,アップロード先のパスが無効です。')

            # 送信ファイルの確認
            file = request.files["file"]
            if not file:
                return redirect(f'./file?p=.&i=e,ファイル名が無効です。')

            # 送信ファイルの書き出し
            file.save(str(FileExplorer.FILE_EXPLORER_ROOT / out_dir / secure_filename(file.filename)))

            # 問題がなければ、アップロード先のフォルダを開かせる
            current_dir = FileExplorer.normalize_path(out_dir)
            return redirect(f"./file?p={current_dir.as_posix()}&i=s,ファイルをアップロードしました。")

        else:  # download
            # 引数の確認
            path = request.args.get("p")
            if path is None or path == '':
                return redirect(f'./file?p=.&i=e,ダウンロードするファイルが指定されていません。')

            # パスの確認
            path = Path(path)
            if not (FileExplorer.FILE_EXPLORER_ROOT / path).exists() or (FileExplorer.FILE_EXPLORER_ROOT / path).is_dir():
                return redirect(f'./file?p=.&i=e,ダウンロードするファイルが無効です。')

            # ファイル出力
            return send_file(FileExplorer.FILE_EXPLORER_ROOT / path, mimetype=mimetypes.guess_extension(path.name))
    else:
        return redirect('login')


@app.route("/fe", methods=["GET", "POST"])
def file_edit():
    """
    ファイルの編集
    引数:
      GET    ./?p=(編集するファイルのパス)
    """
    if check_cookie():
        if request.method == "GET":  # edit
            # 引数の確認
            path = request.args.get("p")  # 編集ファイルの対象パスを指定

            if path is None or path == '':
                return redirect(f'./file?p=./&i=e,編集するファイルのパスが指定されていません。')

            # パスの確認
            path = Path(path)
            if not (FileExplorer.FILE_EXPLORER_ROOT / path).exists() or (FileExplorer.FILE_EXPLORER_ROOT / path).is_dir():
                current_dir = Path(request.args.get("p")).parent
                return redirect(f'./file?p={current_dir}&i=e,編集するファイルのパスが無効です。')

            # ファイル名を取得し、テキストファイルでなければfioに返す
            file_name = Path(request.args.get("p")).name
            if file_name.endswith('.jar' or '.gz' or '.png' or '.jpg' or '.jpeg' or '.gif' or '.webp' or
                                  '.mp4' or '.mov' or '.mp3' or '.m4a' or '.wav'):
                return redirect(f'./fio?p={path}')

            # ファイルの絶対パスを取得
            current_dir = FileExplorer.FILE_EXPLORER_ROOT / path

            # 中身を取得
            try:
                with open(current_dir, 'r', encoding='utf-8') as f:
                    v = f.read()
                    return render_template('edit.html', file=file_name, value=v)

            # UnicodeDecodeErrorが起きたらfioに返す
            except UnicodeDecodeError:
                return redirect(f'./fio?p={path}')

        elif request.method == "POST":
            if request.form['send'] == '保存':

                # 編集ファイルの対象パスを指定
                path = request.args.get("p")

                # ファイルの絶対パスを取得
                current_path = FileExplorer.FILE_EXPLORER_ROOT / path

                # 入力された内容を指定
                value = request.form['value']

                # ファイルに上書き
                with open(current_path, 'w', encoding='utf-8', newline="\n") as f:
                    f.write(value)

                # 編集したファイルのフォルダを開かせる
                current_dir = Path(path).parent
                return redirect(f'./file?p={current_dir}&i=s,ファイルを保存しました。')

            elif request.form['send'] == 'キャンセル':

                path = request.args.get("p")

                # キャンセルしたファイルのフォルダを開かせる
                current_dir = Path(path).parent
                return redirect(f'./file?p={current_dir}')
    else:
        return redirect('login')


@app.route("/fc")
def file_copy():
    """
    ファイルのコピー
    引数:
      GET ./?s=(コピー元)&d=(コピー先)
    """
    if check_cookie():
        # 引数の確認
        source_paths = request.args.get("s")  # コピー元のパス
        to_path = request.args.get("d")  # コピー先のパス

        if source_paths is None or source_paths == '':
            return redirect(f'./file?p=./&i=e,コピーするファイルのパスが指定されていません。')
        if to_path is None or to_path == '':
            return redirect(f'./file?p=./&i=e,コピー先のパスが指定されていません。')

        if ',' in source_paths:
            source_path = source_paths.split(',')
            for p in source_path:

                # パスの確認
                source_path = Path(p)
                if not (FileExplorer.FILE_EXPLORER_ROOT / source_path).exists():
                    current_dir = request.args.get("d")
                    return redirect(f'./file?p={current_dir}&i=e,コピーするファイルのパスが無効です。')
                to_path = Path(to_path)
                if not (FileExplorer.FILE_EXPLORER_ROOT / to_path).exists() or (FileExplorer.FILE_EXPLORER_ROOT / to_path).is_file():
                    current_dir = request.args.get("d")
                    return redirect(f'./file?p={current_dir}&i=e,コピー先のパスが無効です。')

                # コピー先のファイルを参照
                file_name = Path(source_path).name
                current_path = FileExplorer.normalize_path(Path(to_path or FileExplorer.FILE_EXPLORER_ROOT))
                copy_to = current_path / file_name

                # コピー先に同じ名前のファイルがあった場合
                if (FileExplorer.FILE_EXPLORER_ROOT / copy_to).exists():

                    # 語尾にコピーをつける (windows風)
                    file_obj = str(Path(file_name).stem) + " - コピー" + str(Path(file_name).suffix)
                    to_path_copy = to_path / file_obj

                    try:
                        if (FileExplorer.FILE_EXPLORER_ROOT / source_path).is_dir():
                            shutil.copytree(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                                            FileExplorer.FILE_EXPLORER_ROOT / to_path_copy)
                        else:
                            shutil.copy(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                                        FileExplorer.FILE_EXPLORER_ROOT / to_path_copy)
                    except Exception:
                        raise

                else:
                    try:
                        if (FileExplorer.FILE_EXPLORER_ROOT / source_path).is_dir():
                            shutil.copytree(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                                            FileExplorer.FILE_EXPLORER_ROOT / to_path)
                        else:
                            shutil.copy(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                                        FileExplorer.FILE_EXPLORER_ROOT / to_path)
                    except Exception:
                        raise

                # 問題がなければ、コピー先ファイルのフォルダを開かせる
            current_dir = request.args.get("d")
            return redirect(f'./file?p={current_dir}&i=s,ファイルをコピーしました。')

        else:
            if source_paths is None or source_paths == '':
                return redirect(f'./file?p=./&i=e,コピーするファイルのパスが無効です。')
            if to_path is None or to_path == '':
                current_dir = request.args.get("d")
                return redirect(f'./file?p={current_dir}&i=e,コピー先のパスが無効です。')

            # パスの確認
            source_path = Path(source_paths)
            if not (FileExplorer.FILE_EXPLORER_ROOT / source_path).exists():
                current_dir = request.args.get("d")
                return redirect(f'./file?p={current_dir}&i=e,コピーするファイルのパスが無効です。')
            to_path = Path(to_path)
            if not (FileExplorer.FILE_EXPLORER_ROOT / to_path).exists() or (FileExplorer.FILE_EXPLORER_ROOT / to_path).is_file():
                return redirect(f'./file?p=./&i=e,コピー先のパスが無効です。')

            # コピー先のファイルを参照
            file_name = Path(source_path).name
            current_path = FileExplorer.normalize_path(Path(to_path or FileExplorer.FILE_EXPLORER_ROOT))
            copy_to = current_path / file_name

            # コピー先に同じ名前のファイルがあった場合
            if (FileExplorer.FILE_EXPLORER_ROOT / copy_to).exists():
                file_obj = str(Path(file_name).stem) + " - コピー" + str(Path(file_name).suffix)
                to_path_copy = to_path / file_obj

                try:
                    if (FileExplorer.FILE_EXPLORER_ROOT / source_path).is_dir():
                        shutil.copytree(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                                        FileExplorer.FILE_EXPLORER_ROOT / to_path_copy)
                    else:
                        shutil.copy(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                                    FileExplorer.FILE_EXPLORER_ROOT / to_path_copy)
                except Exception:
                    raise

            else:
                # フォルダをコピー
                try:
                    if (FileExplorer.FILE_EXPLORER_ROOT / source_path).is_dir():
                        shutil.copytree(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                                        FileExplorer.FILE_EXPLORER_ROOT / to_path)
                    else:
                        shutil.copy(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                                    FileExplorer.FILE_EXPLORER_ROOT / to_path)
                except Exception:
                    raise

            # 問題がなければ、コピー先ファイルのフォルダを開かせる
            current_dir = request.args.get("d")
            return redirect(f'./file?p={current_dir}&i=s,ファイルをコピ－しました。')
    else:
        return redirect('login')


@app.route("/fm")
def file_move():
    """
    ファイルの移動(カット)
    引数:
      GET ./?s=(移動元)&d=(移動先)
    """
    if check_cookie():
        # 引数の確認
        source_paths = request.args.get("s")  # 移動元のパス
        to_path = request.args.get("d")  # 移動先のパス

        if source_paths is None or source_paths == '':
            return redirect(f'./file?p=.&i=e,切り取りするファイルのパスが指定されていません。')
        if to_path is None or to_path == '':
            return redirect(f'./file?p=.&i=e,切り取り先のパスが指定されていません。')

        # パスが複数ある場合
        if ',' in source_paths:
            for source_path in source_paths.split(','):

                # パスの確認
                source_path = Path(source_path)
                if not (FileExplorer.FILE_EXPLORER_ROOT / source_path).exists():
                    current_dir = request.args.get("d")
                    return redirect(f'./file?p={current_dir}&i=e,切り取りするファイルのパスが無効です。')

                # 移動先がファイルだった場合
                to_path = Path(to_path)
                if (FileExplorer.FILE_EXPLORER_ROOT / to_path).is_file():
                    current_dir = Path(source_path).parent
                    return redirect(f'./file?p={current_dir}&i=e,切り取り先のパスが無効です。')

                # 移動先に同じ名前のファイルがあった場合
                if (FileExplorer.FILE_EXPLORER_ROOT / to_path / source_path.name).exists():
                    current_dir = Path(source_path).parent
                    return redirect(f'./file?p={current_dir}&i=e,既に同じ名前のファイルが存在します。')

                # ファイルの移動
                if source_path.parent != to_path:  # 移動元と移動先が同じだったら何もしない
                    shutil.move(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                                FileExplorer.FILE_EXPLORER_ROOT / to_path / source_path.name)

        else:
            # パスの確認
            source_path = Path(source_paths)
            if not (FileExplorer.FILE_EXPLORER_ROOT / source_path).exists():
                current_dir = Path(request.args.get("d")).parent
                return redirect(f'./file?p={current_dir}&i=e,切り取りするファイルのパスが無効です。')

            # 移動先がファイルだった場合
            to_path = Path(to_path)
            if not (FileExplorer.FILE_EXPLORER_ROOT / to_path).exists() or (FileExplorer.FILE_EXPLORER_ROOT / to_path).is_file():
                current_dir = request.args.get("s")
                return redirect(f'./file?p={current_dir}&i=e,切り取り先のパスが無効です。')

            # 移動先に同じ名前のファイルがあった場合
            if (FileExplorer.FILE_EXPLORER_ROOT / to_path / source_path.name).exists():
                current_dir = Path(source_path).parent
                return redirect(f'./file?p={current_dir}&i=e,既に同じ名前のファイルが存在します。')

            # ファイルの移動
            if source_path.parent != to_path:
                shutil.move(FileExplorer.FILE_EXPLORER_ROOT / source_path,
                            FileExplorer.FILE_EXPLORER_ROOT / to_path / source_path.name)

        # 問題がなければ、移動先ファイルのフォルダを開かせる
        current_dir = request.args.get("d")
        return redirect(f'./file?p={current_dir}&i=s,ファイルを切り取りしました。')
    else:
        return redirect('login')


@app.route("/fd")
def file_delete():
    """
    ファイルの削除
    引数:
      ./?p=(削除するファイルのパス)
    """
    if check_cookie():
        # 引数の確認
        paths = request.args.get("p")  # 削除するファイルパスを指定
        if paths is None or paths == '':
            return redirect('./file?p=.&i=e,パスが指定されていません。')

        # パスが複数あるとき
        if ',' in paths:

            # パスを配列に変換
            path = paths.split(',')

            # 1つずつ処理
            for p in path:
                path = Path(p)
                if not (FileExplorer.FILE_EXPLORER_ROOT / path).exists():
                    current_dir = str(Path(path).parent)
                    return redirect(f'./file?p={current_dir}&i=e,コピー先のパスが無効です。')
                try:
                    if (FileExplorer.FILE_EXPLORER_ROOT / path).is_dir():
                        shutil.rmtree(FileExplorer.FILE_EXPLORER_ROOT / path)
                    else:
                        os.remove(FileExplorer.FILE_EXPLORER_ROOT / path)
                except Exception:
                    raise

                # 問題がなければ、削除ファイルの元フォルダを開かせる
            current_dir = str(Path(path).parent)
            return redirect(f"./file?p={current_dir}&i=s,ファイルを削除しました。")
        else:
            path = Path(paths)
            if not (FileExplorer.FILE_EXPLORER_ROOT / path).exists():
                current_dir = str(Path(path).parent)
                return redirect(f'./file?p={current_dir}&i=e,コピー先のパスが無効です。')
            try:
                if (FileExplorer.FILE_EXPLORER_ROOT / path).is_dir():
                    shutil.rmtree(FileExplorer.FILE_EXPLORER_ROOT / path)
                else:
                    os.remove(FileExplorer.FILE_EXPLORER_ROOT / path)
            except Exception:
                raise

        # 問題がなければ、削除ファイルの元フォルダを開かせる
        current_dir = path.parent
        return redirect(f"./file?p={current_dir}&i=s,ファイルを削除しました。")
    else:
        return redirect('login')


@app.route("/fr")
def file_rename():
    """
    ファイル名の変更
    引数:
      GET ./?p=(変更元)&d=(変更先)
    """
    if check_cookie():
        # 引数の確認
        path = request.args.get("p")  # 変更元のパス
        to_path = request.args.get("d")  # 変更先のパス
        if path is None or path == '':
            return redirect(f'./file?p=.&i=e,ファイル名を変更するファイルのパスが指定されていません。')
        if to_path is None or to_path == '':
            return redirect(f'./file?p=.&i=e,ファイル名を変更する先のパスが指定されていません。')

        # パスの確認
        path = Path(path)
        print(FileExplorer.FILE_EXPLORER_ROOT / path)
        if not (FileExplorer.FILE_EXPLORER_ROOT / path).exists():
            current_dir = Path(request.args.get("p")).parent
            return redirect(f'./file?p={current_dir}&i=e,ファイル名を変更するファイルのパスが無効です。')
        to_path = Path(to_path)

        if (FileExplorer.FILE_EXPLORER_ROOT / to_path).exists():
            current_dir = Path(request.args.get("p")).parent
            return redirect(f'./file?p={current_dir}&i=e,既に同じ名前のファイルがあります。')

        # 名前の変更
        os.rename(FileExplorer.FILE_EXPLORER_ROOT / path, FileExplorer.FILE_EXPLORER_ROOT / to_path)

        # 問題がなければ、変更先ファイルのフォルダを開かせる
        current_dir = Path(request.args.get("p")).parent
        return redirect(f'./file?p={current_dir}&i=s,ファイル名を変更しました。')

    else:
        return redirect('login')


@app.errorhandler(403)
def error_403(error):
    if check_cookie():
        return render_template('403.html')
    else:
        return redirect('login')


@app.errorhandler(404)
def error_404(error):
    if check_cookie():
        return render_template('404.html')
    else:
        return redirect('login')


@app.errorhandler(500)
def error_500(error):
    if check_cookie():
        return render_template('500.html')
    else:
        return redirect('login')


@socketio.on('connect')
def connect():
    global socketio_status
    socketio_status = 'connect'
    t = threading.Thread(target=export_console)
    t.start()


@socketio.on('disconnect')
def disconnect():
    global socketio_status
    socketio_status = 'disconnect'


@socketio.on('console')
def run_command(data):
    ServerJob.exe_command(data['srv'], data['cmd'])
