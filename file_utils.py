import os
import urllib2
import config

class File:
    class PathNotOkError(Exception):
        pass

    class NotFoundError(Exception):
        pass

    def __init__(self, URI):
        self.full_path = self.full_path_by_URI(URI)

        if not os.path.exists(self.full_path):
            if self.is_index:
                raise self.PathNotOkError()
            raise self.NotFoundError()

        if not self.isPathOK(self.full_path):
            raise self.PathNotOkError()

        self.fd = os.open(self.full_path, os.O_RDONLY)
        self.size_bytes = os.fstat(self.fd).st_size
        os.close(self.fd)
        self.fd = None

    def open_if_not_opened(self):
        if self.fd is not None:
            return
        self.fd = os.open(self.full_path, os.O_RDONLY)
        self.size_bytes = os.fstat(self.fd).st_size



    def close_if_not_closed(self):
        if self.fd is None:
            return
        os.close(self.fd)
        self.fd = None

    def isPathOK(self, path):
        if not path.startswith(config.DOCUMENT_ROOT):
            return False
        # if path.find('/../') != -1:
        #     return False
        if not os.access(path, os.R_OK):
            return False
        return True

    def full_path_by_URI(self, URI):
        URI = urllib2.unquote(URI)
        path = config.DOCUMENT_ROOT
        if not URI.startswith('/'):
            path += '/'
        path += URI
        qmark = path.find('?')
        if qmark != -1:
            path = path[:qmark]
        self.is_index = path.endswith('/')
        if self.is_index:  #os.path.isdir(path):
            path += 'index.html'
        path = os.path.realpath(path)
        return path



