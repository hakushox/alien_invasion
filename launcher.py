import requests
import json
import zipfile
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading
import os  # <--- 确保你代码顶部有 import os，如果没有请加上

# ── 终极跨平台路径定位（完美适配 onefile） ──
if getattr(sys, 'frozen', False):
    # 打包后的环境
    if sys.platform == "darwin":
        # 【Mac 专属】无论 launcher 是不是 onefile 打包，
        # Mac 底层都能通过这个环境变量拿到最外层 launcher.app 的绝对路径
        bundle_path = Path(os.environ.get('XPC_SERVICE_NAME', '')).parent
        
        # 兜底：如果没拿到环境变量（比如未完全初始化），用老逻辑
        if not bundle_path or bundle_path == Path('.'):
            ROOT = Path(sys.executable).parent
            if "Contents/MacOS" in str(ROOT):
                TOP_DIR = ROOT.parent.parent.parent
            else:
                TOP_DIR = ROOT
        else:
            # 成功穿透 onefile 临时目录，它的 parent 就是总根目录（比如 /Applications/）
            TOP_DIR = bundle_path.parent
    else:
        # Windows 环境保持原样
        TOP_DIR = Path(sys.executable).parent
else:
    # 未打包的源码开发环境
    TOP_DIR = Path(__file__).parent

GITHUB_API = 'https://api.github.com/repos/hakushox/alien_invasion/releases/latest'

if sys.platform == "win32":
    # ── Windows 环境结构 ──
    GAME_EXE = TOP_DIR / 'Angry Mercy' / 'Angry Mercy.exe'
    LOCAL_VERSION_FILE = GAME_EXE.parent / 'local_version.json'
else:
    # ── Mac 环境精准适配默认打包产物 ──
    # 1. 启动目标直接指向 .app 包内部的二进制文件
    GAME_EXE = TOP_DIR / 'Angry Mercy' / 'Angry Mercy.app' / 'Contents' / 'MacOS' / 'Angry Mercy'    
    # 2. 版本控制 json 文件存放在这个二进制旁边（.app 内部）
    LOCAL_VERSION_FILE = GAME_EXE.parent / 'local_version.json'

# ── 颜色常量 ──
BG = '#0a0a0a'
FG = '#ffffff'
ACCENT = '#e63946'  
BAR_BG = '#1e1e1e'
BAR_FG = '#e63946'

class LauncherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Angry Mercy')
        self.root.geometry('480x220')
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        
        # 居中窗口
        self.root.eval('tk::PlaceWindow . center')

        # 标题
        tk.Label(self.root, text='ANGRY MERCY', font=('Arial', 28, 'bold'),
                 bg=BG, fg=FG).pack(pady=(30, 5))

        # 版本号
        self.version_label = tk.Label(self.root, text='',
                                       font=('Arial', 9), bg=BG, fg='#666666')
        self.version_label.pack()

        # 状态文字
        self.status_label = tk.Label(self.root, text='正在检查更新...',
                                      font=('Arial', 10), bg=BG, fg=FG)
        self.status_label.pack(pady=(20, 5))

        # 进度条
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Red.Horizontal.TProgressbar',
                        troughcolor=BAR_BG, background=BAR_FG, bordercolor=BG)

        self.progress = ttk.Progressbar(self.root, style='Red.Horizontal.TProgressbar',
                                         length=400, mode='determinate')
        self.progress.pack()

        # 后台线程执行更新逻辑，避免卡住 UI
        threading.Thread(target=self.run, daemon=True).start()

        self.root.mainloop()

    def set_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def set_progress(self, value):
        self.root.after(0, lambda: self.progress.config(value=value))

    def set_version(self, text):
        self.root.after(0, lambda: self.version_label.config(text=text))

    def run(self):
        try:
            local = get_local_version()
            self.set_version(f'本地版本: {local or "未安装"}')

            self.set_status('正在检查更新...')
            latest, zip_url = get_latest_release()

            if local != latest:
                if zip_url is None:
                    self.set_status('有新版本但找不到下载链接，直接启动')
                else:
                    self.set_status(f'发现新版本 {latest}，开始下载...')
                    # 【修正】下载文件存放在总根目录下
                    save_path = TOP_DIR / 'update.zip'
                    download_update(zip_url, save_path, self.set_progress, self.set_status)
                    self.set_status('正在解压...')
                    # 【修正】解压到总根目录覆盖旧文件
                    apply_update(save_path, TOP_DIR)
                    save_local_version(latest)
                    self.set_version(f'本地版本: {latest}')
                    self.set_status('更新完成，正在启动...')
            else:
                self.set_status('已是最新版本，正在启动...')

        except requests.exceptions.RequestException:
            self.set_status('网络问题，直接启动游戏')
        except Exception as e:
            self.set_status(f'更新失败：{e}')

        self.root.after(1000, self.launch_and_close)

    def launch_and_close(self):
        launch_game()
        self.root.destroy()


def get_latest_release():
    response = requests.get(GITHUB_API, timeout=10)
    response.raise_for_status()
    data = response.json()
    version = data['tag_name']
    zip_url = None
    for asset in data['assets']:
        if asset['name'].endswith('.zip'):
            zip_url = asset['browser_download_url']
            break
    return version, zip_url

def get_local_version():
    if not LOCAL_VERSION_FILE.exists():
        return None
    with open(LOCAL_VERSION_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('version')

def download_update(zip_url, save_path, progress_cb, status_cb):
    response = requests.get(zip_url, stream=True, timeout=30)
    response.raise_for_status()
    total = int(response.headers.get('content-length', 0))
    downloaded = 0
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                percent = downloaded / total * 100
                progress_cb(percent)
                status_cb(f'下载中... {percent:.1f}%')

def apply_update(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_to)
    zip_path.unlink()

def save_local_version(version):
    with open(LOCAL_VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump({'version': version}, f, indent=4)

def launch_game():
    if not GAME_EXE.exists():
        return
    # Mac 必须以数组形式安全传入字符串路径
    subprocess.Popen([str(GAME_EXE)])


if __name__ == '__main__':
    LauncherApp()