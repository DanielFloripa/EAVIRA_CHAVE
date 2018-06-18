from threading import Thread, RLock
import time

class Teste:
    def __init__(self, time, count):
        self.times = time
        self.count = count
        self.thread_list = dict()
        self.global_time = 0
        self.some_rlock = RLock()

    def sub_worker(self, id):
        with self.some_rlock:
            print("SubWorker started from thread", id)
        while self.times < 10:
            with self.some_rlock:
                print "Subworking... %s at gvt %s" % (self.times, self.global_time)
            self.times += 1
            time.sleep(5)

    def worker(self, id):
        with self.some_rlock:
            print("Worker started from thread", id)
        while self.count < 5:
            with self.some_rlock:
                print("Working... at time", self.global_time)
            tmp_thread = Thread(target=self.sub_worker, args=[self.count])
            tmp_thread.start()
            self.count += 1
            time.sleep(5)
        #raise EnvironmentError("Tired of working")

    def gvt(self, max):
        print "Init GVT"
        for self.global_time in range(max):
            self.global_time += 1

    def run(self):
        gvt = Thread(target=self.gvt, args=[99999999])
        gvt.start()
        gvt.join(0.1)
        time.sleep(1)
        for i in range(10):
            self.thread_list[str(i)] = Thread(name="ThreadChave"+str(i), target=self.worker, args=[i])
            self.thread_list.get(str(i)).start()
            self.thread_list.get(str(i)).join(2)



t = Teste(0, 0)
t.run()

with t.some_rlock:
    print "Valores finais", t.count, t.times, t.global_time
time.sleep(10)
with t.some_rlock:
    print "Valores finais2", t.count, t.times, t.global_time

asd = Thread(target=t.worker, args=[0])