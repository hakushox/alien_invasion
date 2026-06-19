import requests
import json
import zipfile
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.executable).parent
GITHUB_API = 'https://api.github.com/repos/hakushox/alien_invasion/releases/latest'
GAME_EXE = ROOT / 'Angry Mercy' / 'Angry Mercy.exe'
LOCAL_VERSION_FILE = GAME_EXE.parent / 'local_version.json'

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

def download_update(zip_url, save_path):
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
                print(f'\r下载中...{percent:.1f}%', end='')

    print('\n下载完成')

def apply_update(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_to)
    zip_path.unlink()
    print('更新完成')

def save_local_version(version):
    with open(LOCAL_VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump({'version': version}, f, indent=4)

def launch_game():
    if not GAME_EXE.exists():
        print(f'找不到 {GAME_EXE}')
        return
    subprocess.Popen([str(GAME_EXE)])

if __name__ == '__main__':
    try:
        local = get_local_version()
        latest, zip_url = get_latest_release()

        print(f'当前版本：{local} | 最新版本: {latest}')

        if local != latest:
            if zip_url is None:
                print('有新版本但没有找到下载链接，直接启动')
            else:
                save_path = ROOT / 'update.zip'
                download_update(zip_url, save_path)
                apply_update(save_path, ROOT)
                save_local_version(latest)
                print(f'已更新到 {latest}')
        else:
            print(f'{local} 已经是最新版')

    except requests.exceptions.RequestException:
        print('网络问题，直接启动游戏')
    except Exception as e:
        print(f'更新失败：{e}，直接启动游戏')

    launch_game()