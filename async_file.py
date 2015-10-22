import ctypes, os, time, random, file_utils

AIO_LIB_NAME = 'myaiolib.so'
cur_dir = file_utils.get_cur_dir()
lib = ctypes.CDLL(cur_dir + '/' + AIO_LIB_NAME, mode=ctypes.RTLD_GLOBAL)
lib.tryRead.argtypes = [ctypes.c_void_p]
lib.cleanup.argtypes = [ctypes.c_void_p]
lib.askForFile.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
lib.tryRead.restype = ctypes.c_int
lib.askForFile.restype = ctypes.c_void_p

class AsyncFile:
    ALLOC_LIM_BYTES = 512 * 1024 * 1024
    CHUNK_LIM_BYTES = 1024 * 1024
    free_bytes = ALLOC_LIM_BYTES
    STATE_NEW = 0
    STATE_CHUNK_REQUESTED = 1
    STATE_CHUNK_READ = 2
    STATE_DONE = 3

    queue_len = 0
    max_queue = 100000


    def __init__(self, file):
        global lib
        self.lib = lib
        self.aio_pointer = None
        self.state = self.STATE_NEW
        self.offset = 0
        file.open_if_not_opened()
        self.file = file
        self.fd = file.fd
        fsize = file.size_bytes
        if AsyncFile.free_bytes < 0:
            raise Exception()
        if AsyncFile.free_bytes == 0:
            raise NotImplementedError()  # todo
        self.chunk_size = min(fsize, AsyncFile.CHUNK_LIM_BYTES, AsyncFile.free_bytes)

        self.buf = 'q' * (self.chunk_size + 1)
        AsyncFile.free_bytes -= self.chunk_size + 1
        self.q = False
        self.c = 0

    def cancel(self):
        if self.state == self.STATE_DONE:
            return
        self.lib.cleanup(self.aio_pointer)
        self.state = self.STATE_DONE
        self.file.close_if_not_closed()

    def request_first_chunk(self):
        # self.fd = os.open(self.filename, os.O_RDONLY)
        self.aio_pointer = self._request_chunk(self.fd, 0)
        self.state = self.STATE_CHUNK_REQUESTED
        self.offset = 0

    def loop(self):
        if self.q and AsyncFile.queue_len <= self.max_queue:
            self.q = False
            self.aio_pointer = self._request_chunk(self.fd, self.offset)
            self.state = self.STATE_CHUNK_REQUESTED

    def request_next_chunk(self):
        if self.state != self.STATE_CHUNK_READ:
            print self.state
            raise Exception(self.state)
        self.aio_pointer = self._request_chunk(self.fd, self.offset)
        self.state = self.STATE_CHUNK_REQUESTED

    def _request_chunk(self, fd, offset):
        if AsyncFile.queue_len > self.max_queue:
            self.q = True
            return 0
        AsyncFile.queue_len += 1
        aio_pointer = self.lib.askForFile(fd, offset, self.chunk_size, self.buf)
        return aio_pointer

    def try_read_chunk(self):
        self.loop()
        if self.q:
            return None
        if self.state != self.STATE_CHUNK_REQUESTED:
            print self.state
            raise Exception()

        ln = self.lib.tryRead(self.aio_pointer, self.buf)
        if ln != -22:
            AsyncFile.queue_len -= 1
            self.state = self.STATE_CHUNK_READ
            if ln < self.chunk_size:
                self.state = self.STATE_DONE
                self.file.close_if_not_closed()
            else:
                self.offset += self.chunk_size
            if ln == 0:
                return ''
            AsyncFile.free_bytes += self.chunk_size + 1

            return self.buf[:ln]
        else:
            return None

class AsyncFileTest(AsyncFile):


    def __init__(self, fileno):
        os.close(fileno)
        self.c = 0
        self.state = AsyncFile.STATE_NEW
        pass


    def cancel_request(self):
        pass

    def request_first_chunk(self):
        pass

    def loop(self):
        pass

    def request_next_chunk(self):
        pass


    def try_read_chunk(self):
        self.c += 1
        if self.c > 10:
            self.state = AsyncFile.STATE_DONE
        return 'hello'