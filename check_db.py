# =============================================================================
# check_db.py
# Script diagnostik: cek koneksi & tabel di source MSSQL dan destination PostgreSQL
# =============================================================================

import sys
import pyodbc
import psycopg2

from config import (
    DB_HOST, DB_PORT, SRC_DB, SRC_USER, SRC_PASS, ODBC_DRIVER,
    DST_HOST, DST_PORT, DST_DB, DST_USER, DST_PASS, DST_SCHEMA,
    TABLE_SCHEMAS,
)
from db_utils import get_src_connection, get_dst_connection


def check_source():
    print(f"\n{'='*60}")
    print(f"  SOURCE: MSSQL — {SRC_DB} @ {DB_HOST}:{DB_PORT}")
    print(f"{'='*60}")
    try:
        conn = get_src_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            ORDER BY TABLE_SCHEMA, TABLE_TYPE, TABLE_NAME
        """)
        rows = cur.fetchall()
        print(f"  Ditemukan: {len(rows)} tabel/view\n")
        print(f"  {'SCHEMA':<15} {'TIPE':<10} {'NAMA'}")
        print(f"  {'-'*15} {'-'*10} {'-'*30}")
        for schema, name, ttype in rows:
            print(f"  {schema:<15} {ttype:<10} {name}")

        # Cek tabel target
        all_names = {name.upper() for _, name, _ in rows}
        print(f"\n  Pengecekan tabel yang akan di-sync:")
        print(f"  {'-'*50}")
        for key, s in TABLE_SCHEMAS.items():
            tname = s["source_table"]
            found = tname.upper() in all_names
            status = "ADA      " if found else "TIDAK ADA"
            print(f"  [{status}] {tname}")
        conn.close()
    except Exception as e:
        print(f"  [ERROR] Gagal konek ke MSSQL: {e}")


def check_destination():
    print(f"\n{'='*60}")
    print(f"  DESTINATION: PostgreSQL — {DST_DB} @ {DST_HOST}:{DST_PORT}")
    print(f"{'='*60}")
    try:
        conn = get_dst_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """)
        rows = cur.fetchall()
        print(f"  Ditemukan: {len(rows)} tabel/view\n")
        print(f"  {'SCHEMA':<15} {'TIPE':<10} {'NAMA'}")
        print(f"  {'-'*15} {'-'*10} {'-'*30}")
        for schema, name, ttype in rows:
            print(f"  {schema:<15} {ttype:<10} {name}")

        # Cek tabel destination
        all_names = {name.upper() for _, name, _ in rows}
        print(f"\n  Pengecekan tabel destination:")
        print(f"  {'-'*50}")
        for key, s in TABLE_SCHEMAS.items():
            tname = s["dest_table"]
            found = tname.upper() in all_names
            status = "ADA      " if found else "BELUM ADA"
            print(f"  [{status}] {DST_SCHEMA}.{tname}")
        conn.close()
    except Exception as e:
        print(f"  [ERROR] Gagal konek ke PostgreSQL: {e}")


def main():
    check_source()
    check_destination()
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
