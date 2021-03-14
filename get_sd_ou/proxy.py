
import queue
import threading
import urllib.request
from urllib.error import URLError
import time

input_file = 'proxylist.txt'
threads = 3

queue = queue.Queue()
output = []

def proxy_generator():
    whilte True
        whilte len < 10:
            lock release
        lock
        for prox in list
            return proxui
    

class ThreadUrl(threading.Thread):
    """Threaded Url Grab"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            #grabs host from queue
            proxy_info = self.queue.get()

            try:
                proxy_handler = urllib.request.ProxyHandler({'http':proxy_info})
                opener = urllib.request.build_opener(proxy_handler)
                opener.addheaders = [('User-agent','Mozilla/5.0')]
                urllib.request.install_opener(opener)
                sock = urllib.request.urlopen("https://www.sciencedirect.com/", timeout= 7)
                rs = sock.read(1012)
                if b'<h1>Example Domain</h1>' in rs:
                    output.append(('0',proxy_info))
                    print('0',proxy_info)
                else:
                    raise Exception("Not Google")
            except URLError as e:
                output.append(('x',proxy_info))
                print('x',proxy_info)
           
            #signals to queue job is done
            self.queue.task_done()

start = time.time()
def main():

    #spawn a pool of threads, and pass them queue instance 
    for _ in range(5):
        t = ThreadUrl(queue)
        t.setDaemon(True)
        t.start()
    hosts = [host.strip() for host in open(input_file).readlines()]
    for host in hosts:
        queue.put(host)

    #wait on the queue until everything has been processed     
    queue.join()

main()
for proxy,host in output:
    print (proxy,host)

print ("Elapsed Time: %s" % (time.time() - start))