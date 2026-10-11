import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests

from app.domain.judge import Judge
from app.domain.review import Review

# 共有リンクは HEAD が 405 や別の 200 を返すことがある。GET でヘッダだけ見る。
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
DEAD_STATUSES = {401, 404, 410}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
LOGIN_HOSTS = frozenset(
    {
        "accounts.google.com",
        "accounts.youtube.com",
        "login.microsoftonline.com",
        "login.live.com",
        "login.dropbox.com",
        "appleid.apple.com",
    }
)
# 「Sign in」単体は公開の Drive 画面にも出るので使わない。
ACCESS_MARKERS = (
    "you need access",
    "request access",
    "sign in to view",
    "this link has expired",
    "this link is disabled",
    "link has been disabled",
    "the file you are trying to download is no longer available",
)
BLOCKED_HOSTS = frozenset({"localhost", "metadata.google.internal", "metadata"})
MAX_REDIRECTS = 5
HTML_LIMIT = 8192
TIMEOUT_SECONDS = 15


class SubRaw:
    id = "SUB-RAW"

    def applies(self, review: Review) -> bool:
        return review.source == "youtube" and review.raw_url.strip() != ""

    def evaluate(self, review: Review, video: bytes | None, judge: Judge) -> bool:
        """死んでいるリンクとログイン着地だけ False。確認できないときは True。"""
        return not link_is_dead(review.raw_url)


def link_is_dead(raw_url: str) -> bool:
    current = raw_url.strip()
    for _ in range(MAX_REDIRECTS + 1):
        if not _is_safe_url(current):
            return False
        if _is_login_url(current):
            return True
        try:
            response = requests.get(
                current,
                allow_redirects=False,
                stream=True,
                timeout=TIMEOUT_SECONDS,
                headers={"User-Agent": USER_AGENT},
            )
        except requests.RequestException:
            return False
        try:
            if response.status_code in REDIRECT_STATUSES:
                location = response.headers.get("Location", "").strip()
                if location == "":
                    return False
                current = urljoin(current, location)
                continue
            return _response_is_dead(response)
        except requests.RequestException:
            return False
        finally:
            response.close()
    return False


def _response_is_dead(response: requests.Response) -> bool:
    status = response.status_code
    if status in DEAD_STATUSES:
        return True
    if status < 200 or status >= 400:
        return False
    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type.lower():
        return False
    return _html_blocks(response)


def _html_blocks(response: requests.Response) -> bool:
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(1024):
        if not chunk:
            continue
        chunks.append(chunk)
        total += len(chunk)
        if total >= HTML_LIMIT:
            break
    text = b"".join(chunks)[:HTML_LIMIT].decode("utf-8", errors="ignore").lower()
    return any(marker in text for marker in ACCESS_MARKERS)


def _is_login_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").rstrip(".").lower()
    return host in LOGIN_HOSTS


def _is_safe_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.hostname is None:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    if parsed.port not in (None, 443):
        return False
    host = parsed.hostname.rstrip(".").lower()
    if host == "" or host in BLOCKED_HOSTS:
        return False
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        return not _blocked_ip(literal)
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    if len(infos) == 0:
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if _blocked_ip(ip):
            return False
    return True


def _blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return _blocked_ip(ip.ipv4_mapped)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )
