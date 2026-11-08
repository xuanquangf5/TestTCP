"""TCP/UDP transport independent of the desktop interface."""

import re
import socket
import threading
import time


def local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(('192.0.2.1', 80))
            return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'


class NetworkSession:
    def __init__(self, ip, tcp_port, udp_port, log, failed=lambda: None):
        socket.inet_pton(socket.AF_INET, ip)
        if not all(1 <= p <= 65535 for p in (tcp_port, udp_port)):
            raise ValueError('Port phải nằm trong khoảng 1–65535.')
        self.ip, self.tcp_port, self.udp_port = ip, tcp_port, udp_port
        self.log, self.failed = log, failed
        self.stopped = threading.Event()
        self.lock = threading.Lock()
        self.sockets = []
        self.pending = {}
        self.threads = []

    def _socket(self, kind):
        sock = socket.socket(socket.AF_INET, kind)
        sock.settimeout(0.2)
        with self.lock:
            if self.stopped.is_set():
                sock.close()
                raise OSError('Phiên đã dừng.')
            self.sockets.append(sock)
        return sock

    def _thread(self, target, *args):
        thread = threading.Thread(target=target, args=args, daemon=True)
        self.threads.append(thread)
        thread.start()

    def start(self, role):
        try:
            tcp = self._socket(socket.SOCK_STREAM)
            udp = self._socket(socket.SOCK_DGRAM)
            if role == 'server':
                tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                tcp.bind((self.ip, self.tcp_port))
                tcp.listen()
                udp.bind((self.ip, self.udp_port))
                self._thread(self._accept, tcp)
                self._thread(self._udp_server, udp)
                self.log('INFO', f'Server TCP đang nghe tại {self.ip}:{self.tcp_port}')
                self.log('INFO', f'Server UDP đang nghe tại {self.ip}:{self.udp_port}')
            else:
                tcp.settimeout(3)
                tcp.connect((self.ip, self.tcp_port))
                tcp.settimeout(0.2)
                udp.connect((self.ip, self.udp_port))
                self.log('INFO', f'TCP đã kết nối tới {self.ip}:{self.tcp_port}')
                self.log('INFO', f'UDP đích {self.ip}:{self.udp_port}; chờ phản hồi để xác nhận.')
                self._thread(self._tcp_receive, tcp, False, 'server')
                self._thread(self._udp_client, udp)
                self._thread(self._send, tcp, udp)
        except Exception:
            self.stop()
            raise

    def stop(self):
        self.stopped.set()
        with self.lock:
            sockets, self.sockets = self.sockets, []
        for sock in sockets:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()

    def _fatal(self, message):
        if not self.stopped.is_set():
            self.log('ERROR', message)
            self.stop()
            self.failed()

    def _accept(self, listener):
        while not self.stopped.is_set():
            try:
                conn, addr = listener.accept()
                conn.settimeout(0.2)
                with self.lock:
                    if self.stopped.is_set():
                        conn.close()
                        return
                    self.sockets.append(conn)
                peer = f'{addr[0]}:{addr[1]}'
                self.log('INFO', f'TCP client kết nối: {peer}')
                self._thread(self._tcp_receive, conn, True, peer)
            except socket.timeout:
                continue
            except OSError as exc:
                self._fatal(f'TCP accept thất bại: {exc}')
                return

    def _reply(self, message, protocol):
        match = re.fullmatch(r'Hello ' + protocol + r' ([0-9]+)', message)
        if match:
            return f'Okie {protocol} {match[1]}'
        self.log('WARN', f'Gói {protocol} sai định dạng: {message!r}')
        return None

    def _ack(self, message, protocol):
        match = re.fullmatch(r'Okie ' + protocol + r' ([0-9]+)', message)
        if not match:
            self.log('WARN', f'Phản hồi {protocol} sai định dạng: {message!r}')
            return
        with self.lock:
            sent = self.pending.pop((protocol, int(match[1])), None)
        if sent is None:
            self.log('WARN', f'Phản hồi trễ hoặc không khớp gói đang chờ: {message}')

    def _tcp_receive(self, sock, server, peer):
        buffer = b''
        try:
            while not self.stopped.is_set():
                try:
                    data = sock.recv(4096)
                except socket.timeout:
                    continue
                if not data:
                    if server:
                        self.log('INFO', f'TCP client ngắt: {peer}')
                    else:
                        self._fatal('Server đã ngắt kết nối TCP.')
                    return
                buffer += data
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    message = line.decode('utf-8', errors='replace').rstrip('\r')
                    self.log('TCP', f'RECV ← {message} [{peer}]')
                    if server:
                        reply = self._reply(message, 'TCP')
                        if reply:
                            sock.sendall((reply + '\n').encode())
                            self.log('TCP', f'SEND → {reply} [{peer}]')
                    else:
                        self._ack(message, 'TCP')
                if len(buffer) > 65536:
                    raise OSError('Thông điệp TCP vượt 64 KiB, thiếu ký tự xuống dòng.')
        except OSError as exc:
            if not self.stopped.is_set():
                if server:
                    self.log('ERROR', f'TCP client {peer}: {exc}')
                else:
                    self._fatal(f'TCP nhận thất bại: {exc}')
        finally:
            with self.lock:
                if sock in self.sockets:
                    self.sockets.remove(sock)
            sock.close()

    def _udp_server(self, sock):
        while not self.stopped.is_set():
            try:
                data, addr = sock.recvfrom(65535)
                message = data.decode('utf-8', errors='replace')
                self.log('UDP', f'RECV ← {message} [{addr[0]}:{addr[1]}]')
                reply = self._reply(message, 'UDP')
                if reply:
                    sock.sendto(reply.encode(), addr)
                    self.log('UDP', f'SEND → {reply} [{addr[0]}:{addr[1]}]')
            except socket.timeout:
                continue
            except OSError as exc:
                self._fatal(f'UDP server thất bại: {exc}')
                return

    def _udp_client(self, sock):
        while not self.stopped.is_set():
            try:
                message = sock.recv(65535).decode('utf-8', errors='replace')
                self.log('UDP', f'RECV ← {message}')
                self._ack(message, 'UDP')
            except socket.timeout:
                continue
            except OSError as exc:
                if not self.stopped.is_set():
                    self.log('ERROR', f'UDP nhận thất bại: {exc}')
                    self.stopped.wait(0.2)

    def _send(self, tcp, udp):
        counts = {'TCP': 0, 'UDP': 0}
        next_send = time.monotonic()
        turn = 0
        while not self.stopped.is_set():
            now = time.monotonic()
            with self.lock:
                expired = [key for key, sent in self.pending.items() if now - sent >= 5]
                for key in expired:
                    del self.pending[key]
            for protocol, count in expired:
                self.log('WARN', f'{protocol} {count:03d}: không có phản hồi sau 5 giây.')
            if now >= next_send:
                protocol = 'TCP' if turn % 2 == 0 else 'UDP'
                counts[protocol] += 1
                count = counts[protocol]
                message = f'Hello {protocol} {count:03d}'
                with self.lock:
                    self.pending[protocol, count] = now
                try:
                    if protocol == 'TCP':
                        tcp.sendall((message + '\n').encode())
                    else:
                        udp.send(message.encode())
                    self.log(protocol, f'SEND → {message}')
                except OSError as exc:
                    with self.lock:
                        self.pending.pop((protocol, count), None)
                    if protocol == 'TCP':
                        self._fatal(f'TCP gửi thất bại: {exc}')
                        return
                    if not self.stopped.is_set():
                        self.log('ERROR', f'UDP gửi thất bại: {exc}')
                turn += 1
                next_send = max(next_send + 1, time.monotonic())
            self.stopped.wait(0.05)
