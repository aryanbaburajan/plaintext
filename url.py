import socket
import ssl
import base64
import urllib.parse
import util
from dataclasses import dataclass


@dataclass
class Text():
    text: str


@dataclass
class Tag():
    tag: str


class SocketCache:
    def __init__(self):
        self.cache = {}

    def get_socket(self, host, port, use_ssl=False):
        if host in self.cache:
            s = self.cache[host]
            if self.is_socket_closed(s):
                self.remove_socket(s)
            else:
                print("cached " + host)
                return s

        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        s.connect((host, port))

        if use_ssl:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=host)

        self.cache[host] = s
        return s

    def is_socket_closed(self, sock):
        try:
            data = sock.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False
        except ConnectionResetError:
            return True
        except Exception as e:
            print(e)
            return False
        return False

    def remove_socket(self, hostname):
        if hostname in self.cache:
            self.cache[hostname].close()
            del self.cache[hostname]

    def close_sockets(self):
        for s in self.cache.values():
            s.close()
        self.cache.clear()


class URL:
    def __init__(self, url, socket_cache):
        self.url = url
        try:
            self.scheme, self.path = self.parse_url(url)
            self.host, self.port, self.path = self.parse_host_port_path(
                self.path)
        except:
            self.__init__("about:blank", socket_cache)
            return
        self.socket_cache = socket_cache

        print(f"url: {self.url}")
        print(f"scheme: {self.scheme}")
        print(f"host: {self.host}")
        print(f"port: {self.port}")
        print(f"path: {self.path}")
        util.separator()

    def parse_url(self, url):
        if url.startswith("about:"):
            return "about", url[len("about:"):]

        if url.startswith("view-source:"):
            self.view_source = True
            url = url[len("view-source:"):]
        else:
            self.view_source = False

        if url.startswith("data:"):
            return "data", url[len("data:"):]
        else:
            scheme, path = url.split("://", 1)
            assert scheme in ["http", "https", "file"]
            return scheme, path

    def parse_host_port_path(self, url):
        if self.scheme not in ["http", "https"]:
            return "", "", url

        if self.scheme == "http":
            port = 80
        elif self.scheme == "https":
            port = 443

        if "/" not in url:
            url = url + "/"
        host, url = url.split("/", 1)
        path = "/" + url
        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        return host, port, path

    def request(self):
        match self.scheme:
            case "about":
                match self.path:
                    case "blank":
                        return "blank"
            case "file":
                return self.fetch_file()
            case "data":
                return self.fetch_data()
            case scheme if scheme in ["http", "https"]:
                return self.fetch_http_https()

    def fetch_file(self):
        with open(self.path, "r") as f:
            return f.read()

    def fetch_data(self):
        metadata, data = self.path.split(",", 1)
        if metadata.endswith(";base64"):
            return base64.b64decode(data).decode("utf8")
        else:
            return urllib.parse.unquote(data)

    def fetch_http_https(self):
        s = self.socket_cache.get_socket(
            self.host, self.port, self.scheme == "https")

        request = f"GET {self.path} HTTP/1.0\r\n"
        request += f"Host: {self.host}\r\n"
        # request += f"Connection: close\r\n"
        request += f"User-Agent: plaintext\r\n"
        request += "\r\n"
        s.send(request.encode("utf8"))

        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content = response.read(int(
            response_headers["content-length"])) if "content-length" in response_headers else response.read()

        if self.view_source:
            content = content.replace("<", "&lt;").replace(">", "&gt;")

        return content
