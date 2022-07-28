from socket import socket
from time import sleep
from json import dumps as json_dumps
from os import name as os_name

ssl_context = __import__("ssl").create_default_context()

if os_name == "nt":
    set_title = __import__("ctypes").windll.kernel32.SetConsoleTitleW

def parse_batch_response(data, limit):
    index = 10
    status = {}
    for _ in range(limit):
        id_index = data.find(b'"id":', index)
        if id_index == -1:
            break
        index = data.find(b',', id_index + 5)
        group_id = data[id_index + 5 : index]
        index = data.find(b'"owner":', index) + 8
        status[group_id] = (data[index] == 123)
        index += 25
    return status

def find_latest_group_id():
    gid = 0
    sock = make_http_socket(("www.roblox.com", 443))

    def exists(group_id):
        sock.send(f"GET /groups/{group_id}/- HTTP/1.1\nHost:www.roblox.com\n\n".encode())
        resp = sock.recv(1048576)
        return not b"location: https://www.roblox.com/search/groups?keyword=" in resp
    
    try:
        for l in range(8, 0, -1):
            num = int("1" + ("0" * (l - 1)))
            for inc in range(1, 10):
                if inc == 9 or not exists(gid + (num * inc)):
                    gid += num * (inc - 1)
                    break
        return gid
        
    finally:
        shutdown_socket(sock)

def send_webhook(url, **kwargs):
    payload = json_dumps(kwargs, separators=(",", ":"))
    hostname, path = url.split("://", 1)[1].split("/", 1)
    https = url.startswith("https")
    if ":" in hostname:
        hostname, port = hostname.split(":", 1)
        port = int(port)
    else:
        port = 443 if https else 80
    sock = make_http_socket((hostname, port), ssl_wrap=https)
    try:
        sock.send(
            f"POST /{path} HTTP/1.1\r\n"
            f"Host: {hostname}\r\n"
            f"Content-Length: {len(payload)}\r\n"
            "Content-Type: application/json\r\n"
            "\r\n"
            f"{payload}".encode())
        sock.recv(4096)
    finally:
        shutdown_socket(sock)

def make_embed(group_info, date):
    return dict(
        title="CLAIM HERE!",
        description="Found Claimable Group!",
        url=f"https://www.roblox.com/groups/{group_info['id']}",
        fields=[
            dict(name="Group ID", value=group_info["id"]),
            dict(name="Group Name", value=group_info["name"]),
            dict(name="Group Description", value=group_info["description"]),
            dict(name="Group Members", value=group_info["memberCount"])
        ],
        footer=dict(
            color = 0xff4d4d,
            text="By !c3#7213"
        ),
        timestamp=date.isoformat()
    )

def make_http_socket(addr, timeout=5, proxy_addr=None,
                     ssl_wrap=True, hostname=None):    
    sock = socket()
    sock.settimeout(timeout)
    sock.connect(proxy_addr or addr)
    
    try:
        if proxy_addr:
            sock.send(f"CONNECT {addr[0]}:{addr[1]} HTTP/1.1\r\n\r\n".encode())
            connect_resp = sock.recv(4096)
            if not (
                connect_resp.startswith(b"HTTP/1.1 200") or\
                connect_resp.startswith(b"HTTP/1.0 200")
            ):
                raise ConnectionRefusedError

        if ssl_wrap:
            sock = ssl_context.wrap_socket(
                sock, False, False, False, hostname or addr[0])
            sock.do_handshake()

        return sock

    except:
        shutdown_socket(sock)
        raise

def shutdown_socket(sock):
    try:
        sock.shutdown(2)
    except OSError:
        pass
    sock.close()

def slice_list(lst, num, total):
    per = int(len(lst)/total)
    chunk = lst[per * num : per * (num + 1)]
    return chunk

def slice_range(r, num, total):
    per = int((r[1]-r[0]+1)/total)
    return (
        r[0] + (num * per),
        r[0] + ((num + 1) * per)
    )

def update_stats(text):
    if os_name == "nt":
        set_title(f"Group Finder | {text}")
    else:
        print(text)
