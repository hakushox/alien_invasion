
import os
files = []
for root, dirs, filenames in os.walk('.'):
    if '.git' in root:
        continue
    for f in filenames:
        path = os.path.join(root, f)
        size = os.path.getsize(path)
        files.append((size, path))
files.sort(reverse=True)
for size, path in files[:20]:
    print(f'{size//1024:>8} KB  {path}')