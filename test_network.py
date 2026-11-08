import socket
import threading
import time
import unittest

from network import NetworkSession


def free_port(kind):
    with socket.socket(socket.AF_INET, kind) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.sessions = []
        self.tcp = free_port(socket.SOCK_STREAM)
        self.udp = free_port(socket.SOCK_DGRAM)

    def tearDown(self):
        for session in self.sessions:
            session.stop()
        for session in self.sessions:
            for thread in session.threads:
                thread.join(timeout=1)
                self.assertFalse(thread.is_alive(), 'Network worker did not stop')

    def session(self, log=lambda *_: None):
        session = NetworkSession('127.0.0.1', self.tcp, self.udp, log)
        self.sessions.append(session)
        return session

    def test_alternating_independent_counts_and_replies(self):
        self.session().start('server')
        records = []
        ready = threading.Event()

        def log(level, message):
            records.append((time.monotonic(), level, message))
            if message == 'RECV ← Okie UDP 002':
                ready.set()

        client = self.session(log)
        client.start('client')
        self.assertTrue(ready.wait(6), records)
        client.stop()
        sent = [(at, level, msg) for at, level, msg in records if msg.startswith('SEND')]
        self.assertEqual([(level, msg) for _, level, msg in sent[:4]], [
            ('TCP', 'SEND → Hello TCP 001'), ('UDP', 'SEND → Hello UDP 001'),
            ('TCP', 'SEND → Hello TCP 002'), ('UDP', 'SEND → Hello UDP 002')])
        for first, second in zip(sent[:3], sent[1:4]):
            self.assertAlmostEqual(second[0] - first[0], 1, delta=0.3)
        self.assertFalse(any(level == 'ERROR' for _, level, _ in records), records)

    def test_tcp_framing_and_restart(self):
        server = self.session()
        server.start('server')
        with socket.create_connection(('127.0.0.1', self.tcp), timeout=2) as conn:
            conn.sendall(b'Hello TCP 0')
            conn.sendall(b'07\nHello TCP 1234\n')
            stream = conn.makefile('rb')
            self.assertEqual(stream.readline(), b'Okie TCP 007\n')
            self.assertEqual(stream.readline(), b'Okie TCP 1234\n')
            stream.close()
        server.stop()
        for thread in server.threads:
            thread.join(1)
        self.session().start('server')

    def test_udp_bind_failure_releases_tcp(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as occupied:
            occupied.bind(('127.0.0.1', self.udp))
            server = self.session()
            with self.assertRaises(OSError):
                server.start('server')
            self.assertTrue(server.stopped.is_set())
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(('127.0.0.1', self.tcp))

    def test_failed_client_cleans_up(self):
        client = self.session()
        with self.assertRaises(OSError):
            client.start('client')
        self.assertTrue(client.stopped.is_set())
        self.assertEqual(client.sockets, [])


if __name__ == '__main__':
    unittest.main()
