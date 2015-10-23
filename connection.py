import time
import file_utils, os
import socket
import config, http
from async_file import AsyncFile

class Connection:

    RESPONSE_200_OK = 1
    RESPONSE_404_NOT_FOUND = 2
    RESPONSE_405_NOT_ALLOWED = 3
    RESPONSE_403_FORBIDDEN = 4

    STATE_NEED_REQUEST = 1
    STATE_RESPONDING = 2
    STATE_DONE = 3

    FIRST_LINE_LIM_BYTES = 1024

    def __init__(self, socket):
        self.socket = socket
        self.response = ''
        self.request_string = ''
        self.state = self.STATE_NEED_REQUEST
        self.http_URI = None
        self.first_line_received = False
        self.file = None
        self.first_line = None

    def on_socket_event(self):
        self

    def timeout_check(self):
        if time.time() > self.last_event_time:
            self.state = self.STATE_DONE

    def on_recv(self, part):
        self.on_socket_event()
        if self.state != self.STATE_NEED_REQUEST:
            raise Exception()
        self.request_string += part

        if not self.first_line_received:

            if http.line_terminator in self.request_string:

                self.state = self.STATE_RESPONDING
                self.first_line_received = True
                first_line = self.request_string.partition(http.line_terminator)[0]
                self.first_line = http.FirstLineOfHttpRequest(first_line=first_line)
                if self.first_line.request_type == http.FirstLineOfHttpRequest.REQUEST_OTHER:
                    self.response_type = self.RESPONSE_405_NOT_ALLOWED
                else:
                    try:
                        file = file_utils.File(self.first_line.URI)
                        self.response_type = self.RESPONSE_200_OK
                    except file_utils.File.PathNotOkError:
                        self.response_type = self.RESPONSE_403_FORBIDDEN
                    except file_utils.File.NotFoundError:
                        self.response_type = self.RESPONSE_404_NOT_FOUND

                if self.response_type == self.RESPONSE_200_OK:
                    if self.first_line.request_type == http.FirstLineOfHttpRequest.REQUEST_GET:
                        self.file = AsyncFile(file)
                        self.file.request_chunk()
                    elif self.first_line.request_type != http.FirstLineOfHttpRequest.REQUEST_HEAD:
                        raise Exception()
                    self.response = http.get_header_for_file(self.first_line.http_version, file) + http.header_terminator


                else:
                    self.response = http.error_response(self.first_line.http_version, self.response_type)
        else:
            if len(self.request_string) > self.FIRST_LINE_LIM_BYTES:
                self.state = self.STATE_DONE

    def respond(self):
        self.on_socket_event()
        if self.state != self.STATE_RESPONDING:
            raise Exception(self.state)

        if self.file is not None:
            if self.file.state != AsyncFile.STATE_DONE:
                if self.file.state == AsyncFile.STATE_NOT_REQUESTED:
                    self.file.request_chunk()
                else:
                    chunk = self.file.try_read_chunk()
                    if chunk:
                        if chunk == '':
                            self.state = self.STATE_DONE
                            return
                        self.response += chunk
            if len(self.response) == 0 and self.file.state == AsyncFile.STATE_DONE:
                self.state = self.STATE_DONE

        if len(self.response) > 0:
            try:
                sent = self.socket.send(self.response)
                self.response = self.response[sent:]
            except:
                self.state = self.STATE_DONE

        if len(self.response) == 0 and self.file is None:
            self.state = self.STATE_DONE

    def close(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            pass
        except:
            pass
        self.socket.close()
        if self.file:
            if self.file.state != AsyncFile.STATE_DONE:
                self.file.cancel()
        pass
