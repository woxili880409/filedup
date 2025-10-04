#创建一个线程安全的计数进度条
import threading

class ProgressBar:
    def __init__(self, total):
        self.total = total
        self.current = 0
        self.lock = threading.Lock()

    def update(self, step=1):
        with self.lock:
            self.current += step
            print('\r[{0:<{1}}] {2:.2f}%'.format('#' * int(self.current / self.total * 100), 100, self.current / self.total * 100), end='')

    def finish(self):
        print('\r[{0:<{1}}] {2:.2f}%'.format('#' * 100, 100, 100))