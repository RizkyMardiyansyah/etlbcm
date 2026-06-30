# =============================================================================
# db_utils.py - Helper koneksi dan utilitas database
# Source  : MSSQL via pyodbc
# Destination : PostgreSQL via psycopg2
# =============================================================================

import re
import pyodbc
import psycopg2
import psycopg2.extras

from config import (
    DB_HOST, DB_PORT, SRC_DB, SRC_USER, SRC_PASS, ODBC_DRIVER,
    DST_HOST, DST_PORT, DST_DB, DST_USER, DST_PASS,
    MSSQL_TO_PG,
)


# ─── Koneksi Source (MSSQL) ───────────────────────────────────────────────────

def get_src_connection() -> pyodbc.Connection:
    """Buat koneksi pyodbc ke MSSQL (source)."""
    conn_str = (
        f"DRIVER={{{ODBC_DRIVER}}};"
        f"SERVER={DB_HOST},{DB_PORT};"
        f"DATABASE={SRC_DB};"
        f"UID={SRC_USER};"
        f"PWD={SRC_PASS};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=30)


# ─── Koneksi Destination (PostgreSQL) ────────────────────────────────────────

def get_dst_connection() -> psycopg2.extensions.connection:
    """Buat koneksi psycopg2 ke PostgreSQL (destination)."""
    try:
        conn = psycopg2.connect(
            host=DST_HOST,
            port=DST_PORT,
            dbname=DST_DB,
            user=DST_USER,
            password=DST_PASS,
            connect_timeout=30,
        )
        return conn
    except UnicodeDecodeError as e:
        # Server mengirim pesan error (mis. authentication failed) dalam
        # encoding non-UTF8 (locale server bukan en_US/C). psycopg2 gagal
        # men-decode pesan tsb sehingga exception aslinya "ditelan".
        # Ini HAMPIR SELALU berarti kredensial/host/port salah, atau
        # pg_hba.conf di server menolak koneksi dari IP/user ini.
        raise RuntimeError(
            "Gagal connect ke PostgreSQL: server menolak koneksi dan "
            "mengirim pesan error dalam encoding yang tidak bisa dibaca "
            "(biasanya locale server non-UTF8). Penyebab paling umum: "
            "username/password salah, atau pg_hba.conf belum mengizinkan "
            "host ini. Cek kredensial DST_USER/DST_PASS di config.py, dan "
            "pastikan pg_hba.conf di server mengizinkan koneksi dari IP "
            f"client ini ke database '{DST_DB}'. "
            f"(Detail asli: {e})"
        ) from e


# ─── Konversi Tipe Data MSSQL -> PostgreSQL ───────────────────────────────────

def mssql_to_pg_type(mssql_type: str) -> str:
    """
    Konversi string tipe data MSSQL ke ekuivalen PostgreSQL.
    Contoh:
        "NVARCHAR(255)"  -> "VARCHAR(255)"
        "DATETIME"       -> "TIMESTAMP"
        "DECIMAL(18,4)"  -> "NUMERIC(18,4)"
        "INT"            -> "INTEGER"
    """
    # Pisahkan nama tipe dan argumen presisi/panjang: "NVARCHAR(255)" -> ("NVARCHAR", "(255)")
    match = re.match(r"([A-Z0-9_]+)(\(.*\))?", mssql_type.strip().upper())
    if not match:
        return mssql_type  # fallback: kembalikan apa adanya

    base_type = match.group(1)
    precision  = match.group(2) or ""   # e.g. "(255)" atau ""

    pg_base = MSSQL_TO_PG.get(base_type, base_type)

    # Tipe yang sudah termasuk presisi di mapping (MONEY, dll.) -> jangan tambah lagi
    if "(" in pg_base:
        return pg_base

    # Untuk VARCHAR/CHAR/NUMERIC: pertahankan argumen presisi/panjang
    if precision and pg_base in ("VARCHAR", "CHAR", "NUMERIC"):
        return f"{pg_base}{precision}"

    return pg_base


# ─── Quote identifier PostgreSQL ─────────────────────────────────────────────

def qi(name: str) -> str:
    """Bungkus nama kolom/tabel dalam double-quote PostgreSQL."""
    return f'"{name}"'


# ─── Fetch data dari MSSQL ────────────────────────────────────────────────────

def fetch_source_data(
    cursor: pyodbc.Cursor,
    src_schema: str,
    table_name: str,
    col_names: list,
    log,
) -> list:
    """Ambil semua baris dari tabel sumber di MSSQL."""
    full_name = f"[{src_schema}].[{table_name}]"
    cols_sql  = ", ".join(f"[{c}]" for c in col_names)
    log.info(f"[fetch] SELECT {cols_sql} FROM {full_name}")
    cursor.execute(f"SELECT {cols_sql} FROM {full_name}")
    rows = cursor.fetchall()
    log.info(f"[fetch] {len(rows)} baris dibaca dari {SRC_DB}.{src_schema}.{table_name}.")
    return rows


# ─── Ensure table di PostgreSQL ───────────────────────────────────────────────

def ensure_table_exists_pg(
    conn: psycopg2.extensions.connection,
    schema: str,
    table_name: str,
    columns: list,          # list of (col_name, mssql_type)
    primary_key: str | None,
    merge_keys: list | None,
    log,
) -> None:
    """
    Buat tabel di PostgreSQL jika belum ada.
    - Single PK  : definisi PRIMARY KEY inline pada kolom
    - Composite PK: PRIMARY KEY (col1, col2, ...) di akhir CREATE TABLE
    - Tidak ada PK: tabel tanpa constraint PK
    """
    col_defs = []
    pk_cols  = merge_keys if merge_keys else ([primary_key] if primary_key else [])

    for col, mssql_type in columns:
        pg_type  = mssql_to_pg_type(mssql_type)
        not_null = "NOT NULL" if col in pk_cols else "NULL"
        col_defs.append(f"    {qi(col)} {pg_type} {not_null}")

    # Tambahkan constraint PK
    if pk_cols:
        pk_col_list = ", ".join(qi(k) for k in pk_cols)
        col_defs.append(f"    CONSTRAINT pk_{table_name} PRIMARY KEY ({pk_col_list})")

    col_block = ",\n".join(col_defs)
    ddl = f"""
CREATE TABLE IF NOT EXISTS {qi(schema)}.{qi(table_name)} (
{col_block}
);
"""
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    log.info(f"[ensure_table] Tabel '{schema}.{table_name}' sudah tersedia.")


# ─── UPSERT ke PostgreSQL ─────────────────────────────────────────────────────

def upsert_rows_pg(
    conn: psycopg2.extensions.connection,
    schema: str,
    table_name: str,
    col_names: list,
    primary_key: str | None,
    merge_keys: list | None,
    rows: list,
    log,
) -> None:
    """
    UPSERT ke PostgreSQL menggunakan INSERT ... ON CONFLICT DO UPDATE.
    Mendukung single PK maupun composite key.
    Baris dengan nilai NULL pada key column akan di-skip.
    """
    if not rows:
        log.warning("[upsert] Tidak ada data untuk di-sync.")
        return

    conflict_cols = merge_keys if merge_keys else ([primary_key] if primary_key else [])

    # Kolom yang diupdate saat konflik (semua kecuali conflict key)
    update_cols = [c for c in col_names if c not in conflict_cols]

    # Build SQL
    tbl          = f"{qi(schema)}.{qi(table_name)}"
    insert_cols  = ", ".join(qi(c) for c in col_names)
    placeholders = ", ".join("%s" for _ in col_names)
    conflict_str = ", ".join(qi(k) for k in conflict_cols)

    if conflict_cols and update_cols:
        update_set = ", ".join(f"{qi(c)} = EXCLUDED.{qi(c)}" for c in update_cols)
        upsert_sql = (
            f"INSERT INTO {tbl} ({insert_cols}) VALUES ({placeholders}) "
            f"ON CONFLICT ({conflict_str}) DO UPDATE SET {update_set};"
        )
    elif conflict_cols:
        # Tidak ada kolom non-key -> hanya INSERT, abaikan duplikat
        upsert_sql = (
            f"INSERT INTO {tbl} ({insert_cols}) VALUES ({placeholders}) "
            f"ON CONFLICT ({conflict_str}) DO NOTHING;"
        )
    else:
        # Tidak ada PK sama sekali -> INSERT biasa
        upsert_sql = f"INSERT INTO {tbl} ({insert_cols}) VALUES ({placeholders});"

    col_idx_map = {name: i for i, name in enumerate(col_names)}
    processed = skipped = errors = 0

    with conn.cursor() as cur:
        for row in rows:
            # Normalisasi: string "NULL" -> None
            values = [
                None if (v is None or (isinstance(v, str) and v.strip().upper() == "NULL"))
                else v
                for v in row
            ]

            # Skip baris jika ada conflict key yang NULL
            if conflict_cols and any(values[col_idx_map[k]] is None for k in conflict_cols):
                skipped += 1
                log.warning(f"[upsert] Skip baris: conflict key NULL — {dict(zip(conflict_cols, [values[col_idx_map[k]] for k in conflict_cols]))}")
                continue

            try:
                cur.execute(upsert_sql, values)
                processed += 1
            except Exception as e:
                errors += 1
                key_info = {k: values[col_idx_map[k]] for k in conflict_cols} if conflict_cols else {}
                log.error(f"[upsert] Gagal pada key={key_info}: {e}")
                conn.rollback()  # rollback transaksi yang rusak sebelum lanjut

    conn.commit()
    log.info(f"[upsert] Selesai. Diproses={processed}, Diskip={skipped}, Error={errors}.")
