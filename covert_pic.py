from PIL import Image
import os

img = Image.open('images/menu/menu_shop2.png')
bbox = img.getbbox()
cropped = img.crop(bbox)

size = max(cropped.size)
square = Image.new('RGBA', (size, size), (0, 0, 0, 0))
offset = ((size - cropped.width) // 2, (size - cropped.height) // 2)
square.paste(cropped, offset)

sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
square.save(r'C:\Users\Administrator\Desktop\python_arduino\python_works\alien_invasion\images\test.ico', sizes=sizes)

# mac_sizes = [(16,16), (32,32), (64,64), (128,128), (256,256), (512,512)]

# # 3. 直接在当前项目根目录下生成 icon.icns 文件
# output_path = 'icon.icns'
# square.save(output_path, format='ICNS', sizes=mac_sizes)

# print(f"成功！Mac 专用图标已生成在: {os.path.abspath(output_path)}")