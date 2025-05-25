import subprocess
import time
import sys
import os
import signal

SERVER_SCRIPT = "file_server.py"
SERVER_IP = "0.0.0.0"
SERVER_PORT = 6667

def start_server(workers, mode="process"):
    cmd = [
        sys.executable, SERVER_SCRIPT,
        "--ip", SERVER_IP,
        "--port", str(SERVER_PORT),
        "--mode", mode,
        "--workers", str(workers)
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    print(f"[SERVER] Started with {workers} workers (pid={proc.pid})")
    time.sleep(1)
    return proc

def stop_server(proc):
    if proc is not None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)
            print(f"[SERVER] Stopped (pid={proc.pid})")
        except Exception as e:
            print(f"[SERVER] Error stopping: {e}")

if __name__ == "__main__":
    # Example usage
    proc = start_server(5)
    time.sleep(5)
    stop_server(proc)