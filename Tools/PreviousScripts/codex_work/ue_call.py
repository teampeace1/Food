import json
import socket
import sys


request = json.loads(sys.stdin.read())
with socket.create_connection(("127.0.0.1", 12029), timeout=15) as conn:
    conn.settimeout(30)
    conn.sendall(json.dumps(request, ensure_ascii=False).encode("utf-8"))
    chunks = []
    while True:
        part = conn.recv(1048576)
        if not part:
            break
        chunks.append(part)
response = json.loads(b"".join(chunks))
result = response.get("result")
try:
    response["result"] = json.loads(result)
except (TypeError, ValueError):
    pass
json.dump(response, sys.stdout, ensure_ascii=False, indent=2)
