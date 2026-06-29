# =============================================================================
# check_db.py
# Script diagnostik: tampilkan semua tabel & view yang ada di bcmdb
# Jalankan ini dulu untuk verifikasi nama tabel yang benar sebelum sync.
# =============================================================================

import pyodbc
import sys
from config import DB_HOST, DB_PORT, SRC_DB, SRC_USER, SRC_PASS, ODBC_DRIVER

def get_connection():
    conn_str = (
        f"DRIVER={{{ODBC_DRIVER}}};"
        f"SERVER={DB_HOST},{DB_PORT};"
        f"DATABASE={SRC_DB};"
        f"UID={SRC_USER};"
        f"PWD={SRC_PASS};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=30)

def main():
    print(f"\nMenghubungkan ke {SRC_DB} di {DB_HOST}...\n")
    try:
        conn = get_connection()
        cur  = conn.cursor()

        # ── Semua TABLE dan VIEW ──────────────────────────────────────────────
        cur.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            ORDER BY TABLE_SCHEMA, TABLE_TYPE, TABLE_NAME
        """)
        rows = cur.fetchall()

        print(f"{'='*60}")
        print(f"  Database : {SRC_DB}")
        print(f"  Ditemukan: {len(rows)} tabel/view")
        print(f"{'='*60}")
        print(f"  {'SCHEMA':<15} {'TIPE':<10} {'NAMA TABEL/VIEW'}")
        print(f"  {'-'*15} {'-'*10} {'-'*30}")
        for schema, name, ttype in rows:
            print(f"  {schema:<15} {ttype:<10} {name}")

        print(f"{'='*60}")

        # ── Cek spesifik nama tabel yang akan di-sync ─────────────────────────
        target_names = [
            "CMDB_ComputerSystem",
            "CMDB_NetworkInterface",
            "CMDB_OperatingSystem",
            "CMDB_Proccessor",
            "FAMView",
        ]
        print("\n  Pengecekan nama tabel target:")
        print(f"  {'-'*50}")
        all_names = {name.upper() for _, name, _ in rows}
        for t in target_names:
            found = t.upper() in all_names
            status = "ADA     " if found else "TIDAK ADA"
            print(f"  [{status}] {t}")
        print(f"{'='*60}\n")

        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Gagal konek ke database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
