import socket
import json
import base64
import logging
import argparse
import sys
import traceback

server_address = ('127.0.0.1', 6667)

DELIMITER = "\r\n\r\n"

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    try:
        sock.sendall(command_str.encode())
        data_received = ""
        while True:
            data = sock.recv(262144)
            if data:
                data_received += data.decode()
                if DELIMITER in data_received:
                    break
            else:
                break
        # Ambil hanya bagian sebelum delimiter
        data_received = data_received.split(DELIMITER)[0]
        print(f"[CLIENT] RESPONSE RAW: {data_received[:300]} ...")
        hasil = json.loads(data_received)
        return hasil
    except Exception as e:
        logging.warning(f"error during data receiving: {e}")
        traceback.print_exc()
        return False
    finally:
        sock.close()

def remote_list():
    command_str = f"LIST{DELIMITER}"
    hasil = send_command(command_str)
    if hasil and hasil.get('status') == 'OK':
        return hasil['data']
    return None

def remote_get(filename=""):
    command_str = f"GET {filename}{DELIMITER}"
    hasil = send_command(command_str)
    if hasil and hasil.get('status') == 'OK':
        namafile = hasil['data_namafile']
        b64data = hasil['data_file']
        try:
            missing_padding = len(b64data) % 4
            if missing_padding:
                b64data += '=' * (4 - missing_padding)
            isifile = base64.b64decode(b64data)
            with open(namafile, 'wb+') as fp:
                fp.write(isifile)
            return True
        except Exception as e:
            logging.warning(f"Gagal decode base64: {str(e)}")
            traceback.print_exc()
            return False
    return False

def remote_upload(filename=""):
    try:
        with open(filename, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        length = len(content)
        # Sertakan length pada command
        command_str = f"UPLOAD {filename} {length} {content}{DELIMITER}"
        result = send_command(command_str)
        return result and result.get('status') == 'OK'
    except Exception as e:
        logging.warning(f"Gagal upload: {str(e)}")
        traceback.print_exc()
        return False
        S
def remote_delete(filename=""):
    command_str = f"DELETE {filename}{DELIMITER}"
    hasil = send_command(command_str)
    return hasil and hasil.get('status') == 'OK'

def main():
    global server_address
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6667)
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list")
    getp = sub.add_parser("get")
    getp.add_argument("filename")
    upp = sub.add_parser("upload")
    upp.add_argument("filename")
    delp = sub.add_parser("delete")
    delp.add_argument("filename")

    args = parser.parse_args()
    server_address = (args.server, args.port)

    if args.command == "list":
        files = remote_list()
        if files: print("daftar file:", files)
        else: print("Gagal list")
    elif args.command == "get":
        result = remote_get(args.filename)
        print("Sukses download" if result else "Gagal download")
    elif args.command == "upload":
        result = remote_upload(args.filename)
        print("Sukses upload" if result else "Gagal upload")
    elif args.command == "delete":
        result = remote_delete(args.filename)
        print("Sukses hapus" if result else "Gagal hapus")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()