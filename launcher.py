import requests
import json
import zipfile
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading
import os
import stat

# ── 终极跨平台路径定位（完美适配 onefile） ──
if getattr(sys, 'frozen', False):
    if sys.platform == "darwin":
        bundle_path = Path(os.environ.get('XPC_SERVICE_NAME', '')).parent
        if not bundle_path or bundle_path == Path('.'):
            ROOT = Path(sys.executable).parent
            if "Contents/MacOS" in str(ROOT):
                TOP_DIR = ROOT.parent.parent.parent
            else:
                TOP_DIR = ROOT
        else:
            TOP_DIR = bundle_path.parent
    else:
        TOP_DIR = Path(sys.executable).parent
else:
    TOP_DIR = Path(__file__).parent

GITHUB_API = 'https://api.github.com/repos/hakushox/alien_invasion/releases/latest'

# ── 跨平台路径常量定义 ──
if sys.platform == "win32":
    # Windows 环境结构
    GAME_EXE = TOP_DIR / 'Angry Mercy' / 'Angry Mercy.exe'
    LOCAL_VERSION_FILE = GAME_EXE.parent / 'local_version.json'
else:
    # Mac 环境精准适配默认打包产物
    GAME_EXE = TOP_DIR / 'Angry Mercy' / 'Angry Mercy.app' / 'Contents' / 'MacOS' / 'Angry Mercy'    
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
        
        self.root.eval('tk::PlaceWindow . center')

        tk.Label(self.root, text='ANGRY MERCY', font=('Arial', 28, 'bold'),
                 bg=BG, fg=FG).pack(pady=(30, 5))

        self.version_label = tk.Label(self.root, text='',
                                       font=('Arial', 9), bg=BG, fg='#666666')
        self.version_label.pack()

        self.status_label = tk.Label(self.root, text='正在检查更新...',
                                      font=('Arial', 10), bg=BG, fg=FG)
        self.status_label.pack(pady=(20, 5))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Red.Horizontal.TProgressbar',
                        troughcolor=BAR_BG, background=BAR_FG, bordercolor=BG)

        self.progress = ttk.Progressbar(self.root, style='Red.Horizontal.TProgressbar',
                                         length=400, mode='determinate')
        self.progress.pack()

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
                    save_path = TOP_DIR / 'update.zip'
                    download_update(zip_url, save_path, self.set_progress, self.set_status)
                    self.set_status('正在解压...')
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
    if sys.platform == 'win32':
        target = 'win_update.zip'
    else:
        target = 'mac_update.zip'

    zip_url = None
    for asset in data['assets']:
        if asset['name'] == target:
            zip_url = asset['browser_download_url']

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
    """解压更新包并自动赋予 Mac 可执行权限"""
    print("正在解压游戏文件...")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_to)
    
    zip_path.unlink()
    
    # === 核心安全魔法：只有在非 Windows (即 Mac) 环境下才执行赋权 ===
    if sys.platform != "win32" and GAME_EXE.exists():
        st = os.stat(GAME_EXE)
        os.chmod(GAME_EXE, st.st_mode | stat.S_IXUSR)
        print("成功为游戏核心文件赋予了 Mac 执行权限")


def save_local_version(version):
    """保存最新版本号到本地 json"""
    # 确保保存版本文件的父目录（比如大文件夹或 .app 内部）真实存在，防止报错
    LOCAL_VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCAL_VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump({'version': version}, f, indent=4)


def launch_game():
    """验证可执行权限并异步拉起主程序"""
    print(f"正在启动游戏，执行路径: {GAME_EXE}")
    
    if not GAME_EXE.exists():
        print(f"❌ 错误：游戏核心文件不存在：{GAME_EXE}")
        return

    # === 前置物理赋权，阻断权限异常 ===
    if sys.platform != "win32":
        try:
            st = os.stat(GAME_EXE)
            # 强制合并所有者可执行权限位 (0o100)
            os.chmod(GAME_EXE, st.st_mode | stat.S_IXUSR)
            print("权限校验通过：已确认 Mac 可执行属性")
        except Exception as perm_err:
            print(f"⚠️ 警告：无法刷新文件权限: {perm_err}")

    try:
        # 维持工作目录(cwd)上下文，执行异步拉起
        subprocess.Popen([str(GAME_EXE)], cwd=str(GAME_EXE.parent))
        print("进程创建成功，主程序已移交后台。")
    except Exception as e:
        print(f"❌ 进程创建失败，底层错误: {e}")
        
if __name__ == '__main__':
    LauncherApp()