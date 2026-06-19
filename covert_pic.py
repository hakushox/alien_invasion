from PIL import Image

img = Image.open('images/ui/title2.png')
bbox = img.getbbox()
cropped = img.crop(bbox)

size = max(cropped.size)
square = Image.new('RGBA', (size, size), (0, 0, 0, 0))
offset = ((size - cropped.width) // 2, (size - cropped.height) // 2)
square.paste(cropped, offset)

sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
square.save(r'C:\Users\Administrator\Desktop\python_arduino\python_works\alien_invasion\images\test.ico', sizes=sizes)