import socket, select, Queue, time

import os
from connection import Connection

def start_worker(child, server):
    worker = Worker(child, server)
    worker.run()


class Worker:
    EVENT_TIMEOUT_SECONDS = 20
    
    def __init__(self, child, server):
        self.server = server
        self.server.setblocking(0)
        self.isRunning = False
        self.child = child
        self.epoll = select.epoll()
        self.connections = {}

    def run(self):

        if self.isRunning:
            raise Exception()
        self.isRunning = True
        print 'worker started'
        self.loop()

    def loop(self):
        
        mask = select.POLLHUP | select.POLLERR

        self.epoll.register(self.server.fileno(), select.POLLIN | mask)

        while True:
            events = self.epoll.poll(self.EVENT_TIMEOUT_SECONDS)
            for fileno, event in events:
                if fileno == self.server.fileno():
                    try:
                        socket, client_address = self.server.accept()
                        socket.setblocking(0)
                        connection = Connection(socket)
                        self.connections[socket.fileno()] = connection
                        self.epoll.register(socket.fileno(), select.POLLIN | mask)
                        connection.last_event_time = time.time()
                    except:
                        pass
                else:
                    connection = self.connections[fileno]
                    connection.last_event_time = time.time()
                    if event & select.EPOLLERR or event & select.EPOLLHUP:
                        self.drop_connection(connection)
                    if event & select.POLLIN:
                        try:
                            data = connection.socket.recv(4096)
                        except:
                            print 'sock err'
                            self.drop_connection(connection)
                            continue
                        if data and data != '':
                            connection.on_recv(data)

                            if connection.state == connection.STATE_RESPONDING:
                                self.epoll.modify(fileno, select.EPOLLOUT | mask)
                            elif connection.state == connection.STATE_DONE:
                                self.drop_connection(connection)
                                continue
                        else:
                            self.drop_connection(connection)
                            continue

                    elif event & select.EPOLLOUT:
                        connection.respond()
                        if connection.state == connection.STATE_DONE:
                            self.drop_connection(connection)
                            continue

            now = time.time()
            for conn in self.connections.values():
                if now - conn.last_event_time > self.EVENT_TIMEOUT_SECONDS:
                    self.drop_connection(conn)

    def drop_connection(self, conn):

        del self.connections[conn.socket.fileno()]
        self.epoll.unregister(conn.socket.fileno())
        conn.close()
