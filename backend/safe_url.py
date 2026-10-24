"""Fetch untrusted recipe URLs without allowing access to internal services."""

import http.client
import ipaddress
import socket
import ssl
import time

import httpx
from fastapi import HTTPException

MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 5
FETCH_TIMEOUT = 30
_REDIRECTS = {301, 302, 303, 307, 308}
_GLOBAL_IPV6 = ipaddress.ip_network("2000::/3")
_TOO_LARGE = "取得するページのサイズが上限を超えています（2MiB）"
_REQUEST_HEADERS = {
    "Accept": "text/html, application/xhtml+xml, text/plain",
    "Accept-Encoding": "identity",
    "Connection": "close",
}


def _reject(message: str) -> HTTPException:
    return HTTPException(status_code=422, detail=message)


def _validate_url(url: httpx.URL) -> None:
    expected_port = {"http": 80, "https": 443}.get(url.scheme)
    if (
        expected_port is None
        or not url.host
        or url.userinfo
        or "%" in url.host
        or url.port not in (None, expected_port)
    ):
        raise _reject("URLは認証情報を含まない標準ポートのHTTP(S)を指定してください")


def _resolve_public_addresses(host: str, port: int) -> list:
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not addresses:
        raise _reject("URLの接続先を確認できませんでした")
    # Reject the entire DNS answer if even one address is internal. IPv6
    # translation/tunnelling addresses must not provide a route back to IPv4 LANs.
    for family, _, _, _, address in addresses:
        ip = ipaddress.ip_address(address[0])
        if (
            family not in (socket.AF_INET, socket.AF_INET6)
            or not ip.is_global
            or ip.is_multicast
            or ip.is_reserved
            or (ip.version == 6 and (ip not in _GLOBAL_IPV6 or ip.sixtofour or ip.teredo))
        ):
            raise _reject("公開インターネット上のURLのみ取得できます")
    return addresses


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("URL fetch timed out")
    return remaining


class _PinnedConnection(http.client.HTTPConnection):
    def __init__(self, url: httpx.URL, addresses: list, deadline: float):
        super().__init__(url.raw_host.decode("ascii"), url.port or (443 if url.scheme == "https" else 80))
        self._addresses = addresses
        self._deadline = deadline
        self._tls = url.scheme == "https"

    def connect(self) -> None:
        # socket.connect uses the validated numeric sockaddr, never the original
        # hostname. A second DNS lookup would reintroduce DNS rebinding.
        for index, (family, socktype, proto, _, address) in enumerate(self._addresses):
            sock = socket.socket(family, socktype, proto)
            try:
                sock.settimeout(_remaining(self._deadline))
                sock.connect(address)
                if self._tls:
                    context = ssl.create_default_context()
                    context.set_alpn_protocols(["http/1.1"])
                    sock = context.wrap_socket(sock, server_hostname=self.host)
                self.sock = sock
                return
            except OSError:
                sock.close()
                if index == len(self._addresses) - 1:
                    raise


def _open_pinned_connection(url: httpx.URL, deadline: float) -> _PinnedConnection:
    _validate_url(url)
    port = url.port or (443 if url.scheme == "https" else 80)
    addresses = _resolve_public_addresses(url.raw_host.decode("ascii"), port)
    return _PinnedConnection(url, addresses, deadline)


def _send_get(connection: _PinnedConnection, url: httpx.URL) -> None:
    # No environment proxies, cookies or credentials. Keep the
    # original hostname for HTTP Host and TLS SNI/certificate checks.
    connection.request("GET", url.raw_path.decode("ascii"), headers=_REQUEST_HEADERS)


def _redirect_target(response: http.client.HTTPResponse, current: httpx.URL, hop: int) -> httpx.URL:
    location = response.getheader("Location")
    if not location or hop == MAX_REDIRECTS:
        raise _reject("URLのリダイレクトが不正、または回数が多すぎます")
    return current.join(location)


def _validate_response_headers(response: http.client.HTTPResponse) -> None:
    if not 200 <= response.status < 300:
        raise _reject("URLの取得先が正常な応答を返しませんでした")
    if response.getheader("Content-Encoding", "identity").strip().lower() != "identity":
        raise _reject("圧縮されたページは取得できません")
    length = response.getheader("Content-Length")
    if length is not None and (int(length) < 0 or int(length) > MAX_RESPONSE_BYTES):
        raise _reject(_TOO_LARGE)


def _read_bounded_body(
    connection: _PinnedConnection, response: http.client.HTTPResponse, deadline: float
) -> bytes:
    # Do not decompress untrusted bodies. Both Content-Length
    # and streamed/chunked bodies are bounded before HTML parsing.
    body = bytearray()
    while True:
        if connection.sock is not None:
            connection.sock.settimeout(_remaining(deadline))
        else:
            _remaining(deadline)
        chunk = response.read1(min(65536, MAX_RESPONSE_BYTES + 1 - len(body)))
        if not chunk:
            return bytes(body)
        body.extend(chunk)
        if len(body) > MAX_RESPONSE_BYTES:
            raise _reject(_TOO_LARGE)


def _decode_text(response: http.client.HTTPResponse, body: bytes) -> str:
    return httpx.Response(
        200, content=body,
        headers={"Content-Type": response.getheader("Content-Type", "text/html")},
    ).text


def _fetch(url: str) -> str:
    current = httpx.URL(url)
    deadline = time.monotonic() + FETCH_TIMEOUT
    for hop in range(MAX_REDIRECTS + 1):
        connection = _open_pinned_connection(current, deadline)
        try:
            _send_get(connection, current)
            with connection.getresponse() as response:
                if response.status in _REDIRECTS:
                    current = _redirect_target(response, current, hop)
                    continue
                _validate_response_headers(response)
                return _decode_text(response, _read_bounded_body(connection, response, deadline))
        finally:
            connection.close()
    raise _reject("URLの取得に失敗しました")


def fetch_public_page(url: str) -> str:
    """Return a bounded text response; validate and pin every redirect hop."""
    try:
        return _fetch(url)
    except (httpx.InvalidURL, ValueError, OSError, http.client.HTTPException) as exc:
        # Do not disclose internal addresses, resolver details or TLS errors.
        raise _reject("URLの取得に失敗しました") from exc
