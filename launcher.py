import requests
import json
import zipfile
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading

ROOT = Path(sys.executable).parent
GITHUB_API = 'https://api.github.com/repos/hakushox/alien_invasion/releases/latest'
GAME_EXE = ROOT / 'Angry Mercy' / 'Angry Mercy.exe'
LOCAL_VERSION_FILE = GAME_EXE.parent / 'local_version.json'

# ── 颜色常量 ──
BG = '#0a0a0a'
FG = '#ffffff'
ACCENT = '#e63946'  # 红色点缀，跟游戏风格搭
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
                    save_path = ROOT / 'update.zip'
                    download_update(zip_url, save_path, self.set_progress, self.set_status)
                    self.set_status('正在解压...')
                    apply_update(save_path, ROOT)
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
    subprocess.Popen([str(GAME_EXE)])


if __name__ == '__main__':
    LauncherApp()