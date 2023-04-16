from pathlib import Path
import yaml

with open('settings.yml', 'r', encoding="utf-8") as fs:
    settings = yaml.load(fs, Loader=yaml.SafeLoader)
    Root = settings['root-directory']

FILE_EXPLORER_ROOT = Path(Root).resolve()


def is_safe_path(path: Path):
    """
    与えられたパスが安全かチェックする
    """
    try:
        # 一度パスを絶対パス化してから、rootパスで相対パス化する
        # relative_to にrootパスより階層が高いパスが与えられるとValueErrorが発生する
        (FILE_EXPLORER_ROOT / path).resolve().relative_to(FILE_EXPLORER_ROOT)
    except ValueError:
        return False
    return True


def normalize_path(path: Path):
    """
    パスをrootパスからの相対パスに正規化する
    """
    return (FILE_EXPLORER_ROOT / path).resolve().relative_to(FILE_EXPLORER_ROOT)


def sorted_iterdir(path: Path):
    """
    与えられたパスの内容をソートして返す
    並びはフォルダを最優先し、大文字小文字を区別しないアルファベット順 (Windows風)
    """
    return sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
