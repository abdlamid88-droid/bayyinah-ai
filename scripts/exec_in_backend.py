import sys
import json
import http.client
import socket

class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, socket_path):
        super().__init__("localhost")
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)

def docker_exec(container, cmd, stream=True):
    conn = UnixHTTPConnection("/var/run/docker.sock")
    payload = json.dumps({"AttachStdout": True, "AttachStderr": True, "Cmd": cmd})
    conn.request("POST", f"/containers/{container}/exec", payload, {"Content-Type": "application/json"})
    res = conn.getresponse()
    data = json.loads(res.read().decode())
    if "Id" not in data:
        raise RuntimeError(f"Exec create failed: {data}")
    exec_id = data["Id"]

    conn = UnixHTTPConnection("/var/run/docker.sock")
    start_payload = json.dumps({"Detach": False, "Tty": False})
    conn.request("POST", f"/exec/{exec_id}/start", start_payload, {"Content-Type": "application/json"})
    res = conn.getresponse()
    
    # Read multiplexed stream
    output_parts = []
    while True:
        header = res.read(8)
        if not header or len(header) < 8:
            break
        stream_type = header[0]
        size = int.from_bytes(header[4:8], byteorder="big")
        payload_data = res.read(size)
        text = payload_data.decode("utf-8", errors="replace")
        if stream:
            sys.stdout.write(text)
            sys.stdout.flush()
        output_parts.append(text)
    
    return "".join(output_parts)

if __name__ == "__main__":
    cmd = sys.argv[1:] if len(sys.argv) > 1 else ["python3", "/app/scripts/run_benchmark.py"]
    docker_exec("bayyinah_backend", cmd)
