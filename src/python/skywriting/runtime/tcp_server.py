
import skywriting.runtime.pycurl_thread as pct
from skywriting.runtime.producer import get_producer_for_id

import threading
import socket
import os
import ciel
import logging

# This is a lot like the AsyncPushThread in executors.py.
# TODO after paper rush is over: get the spaghettificiation of the streaming code under control

class SocketPusher:
        
    def __init__(self, sock):
        self.sock_obj = sock
        self.bytes_available = 0
        self.bytes_copied = 0
        self.fetch_done = False
        self.pause_threshold = None
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)
        self.thread = threading.Thread(target=self.thread_main)
        
    def result(self, success):
        if not success:
            raise Exception("No way to signal failure to TCP consumers yet!")
        with self.lock:
            self.fetch_done = True
            self.cond.notify_all()

    def progress(self, n_bytes):
        with self.lock:
            self.bytes_available = n_bytes
            if self.pause_threshold is not None and self.bytes_available >= self.pause_threshold:
                self.cond.notify_all()

    def start(self):
        self.thread.start()

    def socket_init(self):
        self.sock_obj.setblocking(True)
        sock_file = self.sock_obj.makefile("r", bufsize=0)
        bits = sock_file.readline().strip().split()
        self.refid = bits[0]
        self.remote_netloc = bits[1]
        self.chunk_size = bits[2]
        sock_file.close()
        producer = get_producer_for_id(output_id)
        if producer is None:
            ciel.log("Got auxiliary TCP connection for bad output %s" % output_id, "TCP_FETCH", logging.WARNING)
            new_sock.sendall("FAIL\n")
            new_sock.close()
            return None
        else:
            return producer.subscribe(self, try_direct=True, consumer_fd=sock_file.fileno())

    def thread_main(self):
        try:
            fd_taken = self.socket_init()
            if fd_taken is None:
                return
            elif fd_taken is True:
                ciel.log("Incoming TCP connection for %s connected directly to producer" % self.refid, "TCP_SERVER", logging.INFO)
                return
            # Otherwise we'll get progress/result callbacks as we follow the producer's on-disk file.
            self.read_filename = producer_filename(self.refid)
            ciel.log("Auxiliary TCP connection for output %s (chunk %s) attached via push thread" % (output_id, chunk_size), "TCP_FETCH", logging.INFO)

            with open(self.read_filename, "r") as input_fp:
                while True:
                    while True:
                        buf = input_fp.read(4096)
                        self.sock_obj.sendall(buf)
                        self.bytes_copied += len(buf)
                        with self.lock:
                            if self.bytes_copied == self.bytes_available and self.fetch_done:
                                ciel.log("Socket-push for %s complete: wrote %d bytes" % (self.refid, self.bytes_copied), "TCP_SERVER", logging.INFO)
                                self.sock_obj.close()
                                return
                            if len(buf) < self.chunk_size:
                                # EOF, for now.
                                break
                    with self.lock:
                        self.pause_threshold = self.bytes_copied + self.chunk_size
                        while self.bytes_available < self.pause_threshold and not self.fetch_done:
                            self.cond.wait()
                        self.pause_threshold = None

        except Exception as e:
            ciel.log("Socket-push-thread died with exception %s" % repr(e), "TCP_FETCH", logging.ERROR)
            try:
                self.sock_obj.close()
            except:
                pass

    def start_direct_write(self):
        # Callback indicating the producer is about to take our socket
        self.sock_obj.sendall("GO\n")

def new_aux_connection(self, new_sock):
    try:
        handler = SocketPusher(new_sock)
        handler.start()
    except Exception as e:
        ciel.log("Error handling auxiliary TCP connection: %s" % repr(e), "TCP_FETCH", logging.ERROR)
        try:
            new_sock.close()
        except:
            pass

class TcpServer:

    def __init__(self, port):
        self.aux_port = port
        ciel.log("Listening for auxiliary connections on port %d" % port, "TCP_FETCH", logging.INFO)
        self.aux_listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.aux_listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.aux_listen_socket.bind(("0.0.0.0", port))
        self.aux_listen_socket.listen(5)
        self.aux_listen_socket.setblocking(False)

    def get_select_fds(self):
        return [self.aux_listen_socket.fileno()], [], []

    def notify_fds(self, read_fds, _, _):
        if self.aux_listen_socket.fileno() in read_fds:
            (new_sock, _) = self.aux_listen_socket.accept()
            new_aux_connection(new_sock)

aux_listen_port = None

def create_tcp_server(port):
    global aux_listen_port
    aux_listen_port = port
    pct.add_event_source(TcpServer(port))

def tcp_server_active():
    return aux_listen_port is not None