import socket
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from threading import Thread
from file_protocol import FileProtocol

fp = FileProtocol()

def process_command(data):
    return fp.proses_string(data)

def handle_client(conn, addr, pool):
    try:
        buffer = b""
        DELIMITER = b"\r\n\r\n"
        # Baca data sampai DELIMITER ditemukan
        while True:
            chunk = conn.recv(262144)
            if not chunk:
                break
            buffer += chunk
            if DELIMITER in buffer:
                break
        if buffer:
            data = buffer.decode()
            header, _, content_rest = data.partition("\r\n\r\n")
            tokens = header.strip().split()
            if tokens[0].upper() == "UPLOAD":
                if len(tokens) < 3:
                    hasil = '{"status": "ERROR", "message": "filename and content required"}'
                else:
                    fname = tokens[1]
                    length = int(tokens[2])
                    content_b64 = " ".join(tokens[3:]) + content_rest
                    while len(content_b64) < length:
                        chunk = conn.recv(262144)
                        if not chunk:
                            break
                        content_b64 += chunk.decode()
                    content_b64 = content_b64[:length]
                    future = pool.submit(fp.fi.upload_file, fname, content_b64)
                    try:
                        future.result()
                        hasil = '{"status": "OK", "message": "Upload success"}'
                    except Exception as e:
                        hasil = f'{{"status": "ERROR", "message": "Upload failed: {e}"}}'
                hasil = hasil + "\r\n\r\n"
                conn.sendall(hasil.encode())
            else:
                # perintah lain tetap pakai pool
                command_data = header.strip()
                future = pool.submit(fp.proses_string, command_data)
                hasil = future.result() + "\r\n\r\n"
                conn.sendall(hasil.encode())
    except Exception as e:
        logging.exception(f"Error: {e}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=6667)
    parser.add_argument("--mode", choices=["thread","process"], default="process")
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()

    logging.warning(f"Server mode: {args.mode} pool, workers={args.workers}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.ip, args.port))
    sock.listen(100)

    Executor = ThreadPoolExecutor if args.mode == "thread" else ProcessPoolExecutor

    with Executor(max_workers=args.workers) as pool:
        while True:
            try:
                conn, addr = sock.accept()
                logging.warning(f"connection from {addr}")
                Thread(target=handle_client, args=(conn, addr, pool)).start()
            except KeyboardInterrupt:
                logging.warning("Shutting down server...")
                break

if __name__ == "__main__":
    main()