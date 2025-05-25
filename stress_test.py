import os
import subprocess
import sys
import time
import random
import string
import csv
import shutil
import argparse
from server_manager import start_server, stop_server

SERVER = "127.0.0.1"
PORT = 6667
OPERATIONS = ["upload", "get"]
VOLUMES = [10*1024*1024, 50*1024*1024, 100*1024*1024]
CLIENT_WORKERS = [1, 5, 50]
SERVER_WORKERS = [1, 5, 50]
RESULTS_CSV = "stress_test_results_process_rev.csv"

def make_file(filename, size):
    with open(filename, "wb") as f:
        f.write(os.urandom(size))

def run_client_worker(op, filename):
    try:
        if op == "upload":
            result = subprocess.run(
                [sys.executable, "file_client_cli.py", "--server", SERVER, "--port", str(PORT), "upload", filename],
                capture_output=True, text=True, timeout=300
            )
        elif op == "get":
            # Jangan hapus file hasil GET, biarkan tetap ada di client
            result = subprocess.run(
                [sys.executable, "file_client_cli.py", "--server", SERVER, "--port", str(PORT), "get", filename],
                capture_output=True, text=True, timeout=300
            )
        else:
            return False
        print(f"[DEBUG] STDOUT: {result.stdout}\n[DEBUG] STDERR: {result.stderr}")
        success = ("Sukses" in result.stdout)
        return success
    except Exception as e:
        print(f"[DEBUG] Exception run_client_worker: {e}")
        return False

def client_stress(op, size, client_workers):
    staticfile = f"staticfile_{size//1024//1024}MB.bin"
    # Untuk upload: buat file statis sekali saja
    if op == "upload" and not os.path.exists(staticfile):
        make_file(staticfile, size)
    # Untuk get: file sudah ada di server (disediakan manual), tidak perlu buat file di client
    successes = 0
    fails = 0
    start = time.time()
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def worker_func(i):
        fname = staticfile
        if op == "upload":
            worker_file = f"worker_{i}_{staticfile}"
            shutil.copy(staticfile, worker_file)
            s = run_client_worker(op, worker_file)
            if os.path.exists(worker_file):
                os.remove(worker_file)
            return s
        else:
            # Untuk GET, JANGAN hapus file hasil download
            s = run_client_worker(op, fname)
            return s

    with ThreadPoolExecutor(max_workers=client_workers) as executor:
        futures = [executor.submit(worker_func, i) for i in range(client_workers)]
        for fut in as_completed(futures):
            s = fut.result()
            if s:
                successes += 1
            else:
                fails += 1
    total_time = time.time() - start
    throughput = (size * successes) / total_time if total_time > 0 else 0
    return total_time, throughput, successes, fails

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="Mulai dari kombinasi ke-berapa (1-based)")
    parser.add_argument("--end", type=int, default=None, help="Sampai kombinasi ke-berapa (1-based, opsional)")
    args = parser.parse_args()

    fieldnames = [
        "No", "Operasi", "Volume (MB)", "Client Worker Pool",
        "Server Worker Pool", "Waktu Total per Client (s)",
        "Throughput per Client (B/s)", "Worker Client Sukses",
        "Worker Client Gagal"
    ]
    nomor = 1
    # Tulis header CSV di awal
    if not os.path.exists(RESULTS_CSV) or args.start == 1:
        with open(RESULTS_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    # Loop kombinasi
    for op in OPERATIONS:
        for size in VOLUMES:
            for cworkers in CLIENT_WORKERS:
                for sworkers in SERVER_WORKERS:
                    if nomor < args.start:
                        nomor += 1
                        continue
                    if args.end is not None and nomor > args.end:
                        print(f"Selesai (nomor kombinasi terakhir: {nomor-1})")
                        return
                    print(f"\n--- Kombinasi ke-{nomor} ---")
                    print(f"Operasi: {op}, Volume: {size//1024//1024} MB, Client Worker Pool: {cworkers}, Server Worker Pool: {sworkers}")
                    proc = start_server(sworkers)
                    time.sleep(2)
                    staticfile = f"staticfile_{size//1024//1024}MB.bin"
                    if op == "upload":
                        if not os.path.exists(staticfile):
                            make_file(staticfile, size)
                    # Untuk GET, asumsikan file sudah ada di server, tidak perlu upload!
                    total_time, throughput, n_success, n_fail = client_stress(op, size, cworkers)
                    print(f"Total waktu per client: {total_time:.2f}s, Throughput: {throughput:.2f} B/s, Sukses: {n_success}, Gagal: {n_fail}")
                    row = {
                        "No": nomor,
                        "Operasi": op,
                        "Volume (MB)": size//1024//1024,
                        "Client Worker Pool": cworkers,
                        "Server Worker Pool": sworkers,
                        "Waktu Total per Client (s)": f"{total_time:.2f}",
                        "Throughput per Client (B/s)": f"{throughput:.2f}",
                        "Worker Client Sukses": n_success,
                        "Worker Client Gagal": n_fail,
                    }
                    # Append hasil ke CSV segera
                    with open(RESULTS_CSV, "a", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writerow(row)
                    nomor += 1
                    stop_server(proc)
                    time.sleep(2)
    print(f"\nHasil rekap kombinasi sudah disimpan ke {RESULTS_CSV}")

if __name__ == "__main__":
    main()