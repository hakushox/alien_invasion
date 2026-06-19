import random

dict1 = {"1": 'a', "2":'b',"3":['2','333']}
print(dict1.values())
print(dict1.keys())

for value in dict1.values():
    print(len(value))

a = round(12551.1234, -2)
print(a)
print(f'{a:,}')

for b in range(1):
    print(b)


    range(0)  # 空的，循环一次都不执行

print(random.randint(1,3))

list1 = [1, 2, 3, 4, 5]
random.shuffle(list1)
print(list1)
list2 = [1, 2, 3, 4, 5]
new_list = random.sample(list2, 2)
print(new_list)
# help(random.random)
# help(min)
# help(abs)
# help(random.randint)
# help(any)

help(getattr)
for i in range(1):
    print(i)
i = sum(1 for t in [2,3] if t <3)
print(i)
i = random.uniform(0.3, 0.7)
print(i)
help(getattr)
t_candidates = []
t_candidates.append((2, 'right'))
print(t_candidates)
for i in range(6, 5, -1):
    print(i)
list1 = [[1, 2], [3, 4], [5,6], [7, 8]]
for a in  list1:
    # print(a)
    for b in a:
        print(b)


from PIL import Image
ico = Image.open(r'c:\Users\Administrator\Desktop\python_arduino\python_works\alien_invasion\images\alien_invasion.ico')
print(ico.info)