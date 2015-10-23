import socket, select, time
import epoll_worker, random
from multiprocessing import Process, Queue, Pipe, reduction
import config
import sys

class Server():
    def __init__(self):
        self.isRunning = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.workers = []
        self.nwork = config.cores
        self.parent, child = Pipe()
        for i in range(0, self.nwork):
            worker = Process(target=epoll_worker.start_worker, args=(child, self.sock))
            self.workers.append(worker)

    def bind_and_listen(self):
        port = config.port
        try:
            self.sock.bind(('127.0.0.1', port))
        except:
            print 'could not bind to port ' + str(port)
            sys.exit()

        self.sock.listen(128)
        print 'listening on port ' + str(port)

    def run(self):
        if self.isRunning:
            raise Exception()
        self.bind_and_listen()
        self.isRunning = True

        self.parent, child = Pipe()
        for worker in self.workers:
            worker.start()
