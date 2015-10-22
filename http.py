from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import os
import connection

line_terminator = '\r\n'
header_terminator = '\r\n\r\n'

class FirstLineOfHttpRequest:
    REQUEST_GET = 1
    REQUEST_HEAD = 2
    REQUEST_OTHER = 3
    http_versions = ['HTTP/1.1', 'HTTP/1.0']


    def __init__(self, first_line):
        parts = first_line.split()

        if (len(parts) != 3):
            self.request_type = self.REQUEST_OTHER
            return
        for version in self.http_versions:
            if first_line.lower().endswith(version.lower()):
                self.http_version = version
                break
        if self.http_version is None:
            self.request_type = self.REQUEST_OTHER
            return
        self.URI = parts[1]
        if first_line.lower().startswith('get'):
            self.request_type = self.REQUEST_GET
        elif first_line.lower().startswith('head'):
            self.request_type = self.REQUEST_HEAD
        else:
            self.request_type = self.REQUEST_OTHER


def get_header_for_file(http_version, file):
    header = http_version + ' 200 OK' + line_terminator
    header += 'Content-Type: ' + contentTypeByName(file.full_path) + line_terminator
    header += 'Content-Length: ' + str(file.size_bytes) + line_terminator
    header += 'Last-Modified: ' + get_date_of_file(file.full_path) + line_terminator
    header += get_general_header(http_version)

    return header

def get_general_header(http_version):
    header = 'Server: My HTTP server' + line_terminator
    header += 'Date: ' + get_http_date() + line_terminator
    header += 'Connection: close'
    return header



def get_http_date():
    date_time = datetime.now()
    stamp = mktime(date_time.timetuple())
    return format_date_time(stamp)

def contentTypeByName(path):
    typeDict = {
        '.html' : 'text/html',
        '.css' : 'text/css',
        '.js' : 'application/javascript',
        '.jpg' : 'image/jpeg',
        '.jpeg' : 'image/jpeg',
        '.png' : 'image/png',
        '.gif' : 'image/gif',
        '.swf' : 'application/x-shockwave-flash'
    }
    low = path.lower()
    for x in typeDict.keys():
        if low.endswith(x):
            return typeDict[x]
    return 'text/plain'

def get_date_of_file(filename):
    time = os.path.getmtime(filename)
    date_time = datetime.fromtimestamp(time)
    stamp = mktime(date_time.timetuple())
    return format_date_time(stamp)



def error_response(http_version, response_type):
    resp = http_version + ' '
    if response_type == connection.Connection.RESPONSE_405_NOT_ALLOWED:
        resp += '405 NOT ALLOWED'
    elif response_type == connection.Connection.RESPONSE_404_NOT_FOUND:
        resp += '404 NOT FOUND'
    elif response_type == connection.Connection.RESPONSE_403_FORBIDDEN:
        resp += '403 FORBIDDEN'
    else:
        raise Exception()
    resp += line_terminator + get_general_header(http_version) + header_terminator
    return resp


