# =============================================================================
# diag_pg_raw.py
# Diagnostik low-level: connect socket mentah ke PostgreSQL untuk melihat
# pesan error ASLI dari server (sebelum di-decode psycopg2), supaya kita
# tahu kenapa UnicodeDecodeError muncul saat psycopg2.connect().
# =============================================================================

import socket
import struct

from config import DST_HOST, DST_PORT, DST_DB, DST_USER, DST_PASS

def send_startup(sock, dbname, user):
    params = {
        "user": user,
        "database": dbname,
        "client_encoding": "UTF8",
    }
    body = b""
    for k, v in params.items():
        body += k.encode() + b"\x00" + v.encode() + b"\x00"
    body += b"\x00"
    # protocol version 3.0
    packet = struct.pack("!i", 196608) + body
    length = struct.pack("!i", len(packet) + 4)
    sock.sendall(length + packet)

def main():
    print(f"Connecting raw TCP socket ke {DST_HOST}:{DST_PORT} ...")
    sock = socket.create_connection((DST_HOST, DST_PORT), timeout=10)
    send_startup(sock, DST_DB, DST_USER)

    sock.settimeout(10)
    data = b""
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass

    print(f"\nTotal bytes diterima dari server: {len(data)}")
    print(f"\n--- RAW BYTES (repr) ---")
    print(repr(data))

    print(f"\n--- HEX DUMP ---")
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"{i:04x}  {hex_part:<48}  {ascii_part}")

    print(f"\n--- Coba decode sebagai latin-1 (selalu berhasil) ---")
    print(data.decode("latin-1", errors="replace"))

    sock.close()

if __name__ == "__main__":
    main()
