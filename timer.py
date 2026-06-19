#
#

import time

def timer(func):
    def wrapper(self, *args, **kwargs):
        t = time.time()
        func(self, *args, **kwargs)
        print(f'{func} runs for {time.time()-t:2f}s')
    return wrapper


