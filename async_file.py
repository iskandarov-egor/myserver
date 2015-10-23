import ctypes, utils

AIO_LIB_NAME = 'myaiolib.so'
lib = ctypes.CDLL(utils.cur_dir + '/' + AIO_LIB_NAME, mode=ctypes.RTLD_GLOBAL)
lib.tryRead.argtypes = [ctypes.c_void_p]
lib.cleanup.argtypes = [ctypes.c_void_p]
lib.askForFile.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
lib.tryRead.restype = ctypes.c_int
lib.askForFile.restype = ctypes.c_void_p

class AsyncFile:
    ALLOC_LIM_BYTES = 512 * 1024 * 1024
    CHUNK_LIM_BYTES = 1024 * 1024
    CHUNK_MIN_BYTES = 1024
    free_bytes = ALLOC_LIM_BYTES
    STATE_REQUESTED = 1
    STATE_NOT_REQUESTED = 2
    STATE_DONE = 3
    STATE_QUEUED = 4

    queue_len = 0
    max_queue = 100000


    def __init__(self, file):
        global lib
        self.lib = lib
        self.aio_pointer = None
        self.state = self.STATE_NOT_REQUESTED
        self.offset = 0
        file.open_if_not_opened()
        self.file = file
        self.fd = file.fd


        self.q = False
        self.offset = 0

    def cancel(self):
        if self.state == self.STATE_DONE:
            return
        self.lib.cleanup(self.aio_pointer)
        self.state = self.STATE_DONE
        self.file.close_if_not_closed()

    def request_chunk(self):
        if self.state not in [self.STATE_NOT_REQUESTED, self.STATE_QUEUED]:
            raise Exception(self.state)


        fsize = self.file.size_bytes
        if AsyncFile.free_bytes < 0:
            raise Exception()
        if AsyncFile.free_bytes < self.CHUNK_MIN_BYTES:
            # raise NotImplementedError()  # todo
            self.state = self.STATE_QUEUED
        else:
            self.chunk_size = min(fsize, AsyncFile.CHUNK_LIM_BYTES, AsyncFile.free_bytes)
            self.buf = 'q' * (self.chunk_size + 1)
            AsyncFile.free_bytes -= self.chunk_size + 1
            self.state = self.STATE_REQUESTED
        self.aio_pointer = self.lib.askForFile(self.fd, self.offset, self.chunk_size, self.buf)


    def loop(self):
        if self.q and AsyncFile.queue_len <= self.max_queue:
            self.q = False
            self.aio_pointer = self._request_chunk(self.fd, self.offset)
            self.state = self.STATE_REQUESTED

    def try_read_chunk(self):
        if self.state != self.STATE_REQUESTED:
            raise Exception(self.state)

        if self.state == self.STATE_QUEUED:
            if self.free_bytes > self.CHUNK_MIN_BYTES:
                self.request_chunk()
            else:
                return None

        ln = self.lib.tryRead(self.aio_pointer, self.buf)
        if ln != -22:
            AsyncFile.queue_len -= 1
            self.state = self.STATE_NOT_REQUESTED
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