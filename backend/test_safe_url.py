import io
import socket
import ssl
import unittest
from unittest.mock import patch

from fastapi import HTTPException

import recipe_ai
import safe_url


def address(ip="93.184.215.14", port=80):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    target = (ip, port, 0, 0) if family == socket.AF_INET6 else (ip, port)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", target)


def response(body=b"<html><body>recipe</body></html>", status="200 OK", headers=None):
    fields = {"Content-Length": str(len(body)), "Content-Type": "text/html; charset=utf-8"}
    fields.update(headers or {})
    return (f"HTTP/1.1 {status}\r\n" + "".join(f"{k}: {v}\r\n" for k, v in fields.items()) + "\r\n").encode() + body


class FakeSocket:
    def __init__(self, reply):
        self.reply = reply
        self.sent = bytearray()
        self.destination = None
        self.closed = False

    def connect(self, destination):
        self.destination = destination

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, data):
        self.sent.extend(data)

    def makefile(self, *args):
        return io.BytesIO(self.reply)

    def close(self):
        self.closed = True


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.dns = patch("safe_url.socket.getaddrinfo", return_value=[address()]).start()
        self.socket_factory = patch("safe_url.socket.socket").start()
        self.sockets = []
        self.replies = [response()]

        def make_socket(*args):
            sock = FakeSocket(self.replies.pop(0))
            self.sockets.append(sock)
            return sock

        self.socket_factory.side_effect = make_socket
        self.addCleanup(patch.stopall)

    def rejected(self, url):
        with self.assertRaises(HTTPException) as caught:
            safe_url.fetch_public_page(url)
        self.assertEqual(caught.exception.status_code, 422)

    def test_invalid_urls_rejected_before_dns(self):
        for url in ["file:///etc/passwd", "ftp://example.com/", "//example.com/", "http://",
                    "http://user:password@example.com/", "https://example.com:8443/",
                    "http://example.com:443/", "http://[fe80::1%25eth0]/", "http://[broken/"]:
            with self.subTest(url=url):
                self.rejected(url)
        self.dns.assert_not_called()
        self.socket_factory.assert_not_called()

    def test_private_and_special_addresses_rejected(self):
        for ip in ["127.0.0.1", "10.0.0.1", "172.16.0.1", "192.168.1.1", "169.254.169.254",
                   "0.0.0.0", "100.64.0.1", "224.0.0.1", "255.255.255.255", "192.0.2.1",
                   "::1", "::", "fc00::1", "fe80::1", "ff02::1", "::ffff:127.0.0.1",
                   "64:ff9b::7f00:1", "2002:7f00:1::", "2001:0000:4136:e378:8000:63bf:3fff:fdd2"]:
            with self.subTest(ip=ip):
                self.dns.return_value = [address(ip)]
                self.rejected("http://recipe.example/")
        self.socket_factory.assert_not_called()

    def test_mixed_public_and_private_dns_rejected(self):
        self.dns.return_value = [address(), address("::1")]
        self.rejected("http://recipe.example/")
        self.socket_factory.assert_not_called()

    def test_numeric_host_aliases_are_checked_after_resolution(self):
        self.dns.return_value = [address("127.0.0.1")]
        for host in ["2130706433", "0177.0.0.1", "0x7f000001", "localhost"]:
            self.rejected(f"http://{host}/")
        self.socket_factory.assert_not_called()

    def test_request_pins_ip_and_preserves_host_without_proxy(self):
        self.dns.side_effect = [[address()], [address("127.0.0.1")]]
        with patch.dict("os.environ", {"HTTP_PROXY": "http://127.0.0.1:9999"}):
            self.assertIn("recipe", safe_url.fetch_public_page("http://recipe.example/path?q=1#fragment"))
        self.assertEqual(self.dns.call_count, 1)
        self.assertEqual(self.sockets[0].destination, ("93.184.215.14", 80))
        self.assertIn(b"GET /path?q=1 HTTP/1.1\r\n", self.sockets[0].sent)
        self.assertIn(b"Host: recipe.example\r\n", self.sockets[0].sent)
        self.assertTrue(self.sockets[0].closed)

    def test_https_keeps_certificate_verification_and_sni(self):
        self.dns.return_value = [address(port=443)]
        context = ssl.create_default_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        with patch("safe_url.ssl.create_default_context", return_value=context), \
             patch.object(context, "wrap_socket", side_effect=lambda sock, **kw: sock) as wrap:
            safe_url.fetch_public_page("https://recipe.example/")
        self.assertEqual(wrap.call_args.kwargs, {"server_hostname": "recipe.example"})
        self.assertEqual(self.sockets[0].destination, ("93.184.215.14", 443))

    def test_certificate_failure_is_not_ignored(self):
        context = ssl.create_default_context()
        with patch("safe_url.ssl.create_default_context", return_value=context), \
             patch.object(context, "wrap_socket", side_effect=ssl.SSLCertVerificationError("test")):
            self.rejected("https://recipe.example/")
        self.assertTrue(self.sockets[0].closed)

    def test_internal_redirect_is_blocked_before_second_connection(self):
        self.replies = [response(status="302 Found", headers={"Location": "http://127.0.0.1/"})]
        self.dns.side_effect = [[address()], [address("127.0.0.1")]]
        self.rejected("http://recipe.example/")
        self.assertEqual(len(self.sockets), 1)
        self.assertTrue(self.sockets[0].closed)

    def test_same_host_redirect_revalidates_dns(self):
        self.replies = [response(status="302 Found", headers={"Location": "/next"})]
        self.dns.side_effect = [[address()], [address("10.0.0.1")]]
        self.rejected("http://recipe.example/")
        self.assertEqual(len(self.sockets), 1)

    def test_public_redirect_and_html_extraction_still_work(self):
        self.replies = [response(status="302 Found", headers={"Location": "/recipe"}),
                        response("<html><nav>ignore</nav><body>材料：米<script>ignore</script></body></html>".encode())]
        self.assertEqual(recipe_ai._fetch_page_text("http://recipe.example/"), "材料：米")
        self.assertEqual(self.dns.call_count, 2)
        self.assertTrue(all(sock.closed for sock in self.sockets))

    def test_unsafe_redirect_schemes_and_ports_rejected(self):
        for location in ["file:///etc/passwd", "http://recipe.example:8080/", "http://user:pw@recipe.example/"]:
            with self.subTest(location=location):
                self.replies = [response(status="302 Found", headers={"Location": location})]
                before = len(self.sockets)
                self.rejected("http://recipe.example/")
                self.assertEqual(len(self.sockets), before + 1)

    def test_redirect_loop_is_bounded(self):
        self.replies = [response(status="302 Found", headers={"Location": "/"})] * 6
        self.rejected("http://recipe.example/")
        self.assertEqual(len(self.sockets), 6)

    def test_content_length_limit(self):
        self.replies = [response(headers={"Content-Length": str(safe_url.MAX_RESPONSE_BYTES + 1)})]
        self.rejected("http://recipe.example/")
        self.assertTrue(self.sockets[0].closed)

    def test_chunked_body_limit_without_content_length(self):
        body = b"x" * (safe_url.MAX_RESPONSE_BYTES + 1)
        self.replies = [b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n" +
                        f"{len(body):x}\r\n".encode() + body + b"\r\n0\r\n\r\n"]
        self.rejected("http://recipe.example/")

    def test_exact_size_limit_is_allowed(self):
        body = b"x" * safe_url.MAX_RESPONSE_BYTES
        self.replies = [response(body)]
        self.assertEqual(len(safe_url.fetch_public_page("http://recipe.example/")), len(body))

    def test_body_limit_without_length_or_chunking(self):
        self.replies = [b"HTTP/1.0 200 OK\r\n\r\n" + b"x" * (safe_url.MAX_RESPONSE_BYTES + 1)]
        self.rejected("http://recipe.example/")

    def test_public_ipv6_is_allowed(self):
        self.dns.return_value = [address("2606:4700:4700::1111")]
        self.assertIn("recipe", safe_url.fetch_public_page("http://recipe.example/"))
        self.assertEqual(self.sockets[0].destination, ("2606:4700:4700::1111", 80, 0, 0))

    def test_failed_public_address_falls_back_only_to_validated_address(self):
        self.dns.return_value = [address(), address("1.1.1.1")]
        failed = FakeSocket(b"")
        succeeded = FakeSocket(response())
        self.socket_factory.side_effect = [failed, succeeded]
        with patch.object(failed, "connect", side_effect=ConnectionRefusedError):
            self.assertIn("recipe", safe_url.fetch_public_page("http://recipe.example/"))
        self.assertTrue(failed.closed)
        self.assertTrue(succeeded.closed)
        self.assertEqual(succeeded.destination, ("1.1.1.1", 80))
        self.assertEqual(self.dns.call_count, 1)

    def test_compression_is_not_decoded(self):
        self.replies = [response(b"not even a valid gzip", headers={"Content-Encoding": "gzip"})]
        self.rejected("http://recipe.example/")

    def test_errors_do_not_disclose_internal_details(self):
        self.dns.side_effect = socket.gaierror("private resolver info")
        with self.assertRaises(HTTPException) as caught:
            safe_url.fetch_public_page("http://recipe.example/")
        self.assertNotIn("private resolver info", caught.exception.detail)

    def test_expired_deadline_does_not_connect(self):
        with patch("safe_url.time.monotonic", side_effect=[0, 31]):
            self.rejected("http://recipe.example/")
        self.assertIsNone(self.sockets[0].destination)
        self.assertTrue(self.sockets[0].closed)

    def test_blocked_url_does_not_reach_ai(self):
        self.dns.return_value = [address("127.0.0.1")]
        with patch("recipe_ai.chat_json") as ai:
            with self.assertRaises(HTTPException):
                recipe_ai.import_recipe_from_url("http://localhost/")
        ai.assert_not_called()


if __name__ == "__main__":
    unittest.main()
