
import random
import threading
import time
import logging
logging.basicConfig(level=logging.DEBUG, format='(%(threadName)s) %(message)s')

class ActivePool(object):
    def __init__(self):
        super(ActivePool, self).__init__()
        self.active = []
        self.lock = threading.Lock()
    def makeActive(self, name):
        with self.lock:
            self.active.append(name)
            logging.debug('Append: %s', self.active)
    def makeInactive(self, name):
        with self.lock:
            self.active.remove(name)
            logging.debug('Remove: %s', self.active)

    def worker(self, i, s):
        logging.debug('Waiting to join the pool')
        with s:
            name = threading.currentThread().getName()
            self.makeActive(name)
            time.sleep(0.1)
            self.makeInactive(name)

    def run2(self):
        s = threading.Semaphore(2)
        for i in range(10):
            t = threading.Thread(target=self.worker, name=str('n'+str(i)), args=(i, s))
            t.start()

pool = ActivePool()
pool.run2()