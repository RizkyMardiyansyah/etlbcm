# =============================================================================
# sync_processor.py
# Sinkronisasi tabel CMDB_Proccessor: bcmdb (sa) -> GRAFANADB (grafanauser)
# Logic : SELECT dari bcmdb -> MERGE (UPSERT) ke GRAFANADB
#         Composite key: DeviceID + ProcessorID
#         Jika tabel belum ada di GRAFANADB -> CREATE TABLE otomatis
# Scheduler Windows : jalankan script ini via Task Scheduler
# =============================================================================

import pyodbc
import logging
import sys
from datetime import datetime
from config import DB_HOST, DB_PORT, SRC_DB, SRC_USER, SRC_PASS, \
                   DST_DB, DST_USER, DST_PASS, ODBC_DRIVER, TABLE_SCHEMAS, \
                   SRC_SCHEMA, DST_SCHEMA

# ─── Logging ─────────────────────────────────────────────────────────────────
LOG_FILE = f"sync_processor_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

TABLE_KEY  = "Atrium_CMDB_Processor"
SCHEMA     = TABLE_SCHEMAS[TABLE_KEY]
COLUMNS    = SCHEMA["columns"]
COL_NAMES  = [c[0] for c in COLUMNS]
MERGE_KEYS = SCHEMA["merge_keys"]   # ["DeviceID", "InstanceName"]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_connection(database: str, user: str, password: str) -> pyodbc.Connection:
    conn_str = (
        f"DRIVER={{{ODBC_DRIVER}}};"
        f"SERVER={DB_HOST},{DB_PORT};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, timeout=30)


def ensure_table_exists(cursor: pyodbc.Cursor, table_name: str) -> None:
    """Buat tabel CMDB_Proccessor jika belum ada, dengan composite PK."""
    col_defs = ",\n    ".join(
        f"[{col}] {dtype} {'NOT NULL' if col in MERGE_KEYS else 'NULL'}"
        for col, dtype in COLUMNS
    )
    pk_cols = ", ".join(f"[{k}]" for k in MERGE_KEYS)
    ddl = f"""
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_CATALOG = '{DST_DB}'
      AND TABLE_SCHEMA  = '{DST_SCHEMA}'
      AND TABLE_NAME    = '{table_name}'
)
BEGIN
    CREATE TABLE [{DST_SCHEMA}].[{table_name}] (
        {col_defs},
        CONSTRAINT [PK_{table_name}] PRIMARY KEY ({pk_cols})
    );
    PRINT 'Tabel {table_name} berhasil dibuat.';
END
"""
    cursor.execute(ddl)
    cursor.connection.commit()
    log.info(f"[ensure_table] Tabel '{table_name}' sudah tersedia di {DST_DB}.")


def fetch_source_data(cursor: pyodbc.Cursor, table_name: str) -> list:
    full_name = f"[{SRC_SCHEMA}].[{table_name}]"
    log.info(f"[fetch] Query: SELECT ... FROM {full_name}")
    cursor.execute(f"SELECT {', '.join(f'[{c}]' for c in COL_NAMES)} FROM {full_name}")
    rows = cursor.fetchall()
    log.info(f"[fetch] Berhasil membaca {len(rows)} baris dari {SRC_DB}.{SRC_SCHEMA}.{table_name}.")
    return rows


def upsert_rows(cursor: pyodbc.Cursor, table_name: str, rows: list) -> None:
    """
    UPSERT dengan composite key DeviceID + ProcessorID.
    Baris yang salah satu composite key-nya NULL akan di-skip.
    """
    if not rows:
        log.warning("[upsert] Tidak ada data untuk di-sync.")
        return

    non_key_cols = [c for c in COL_NAMES if c not in MERGE_KEYS]
    update_set   = ", ".join(f"T.[{c}] = S.[{c}]" for c in non_key_cols)
    insert_cols  = ", ".join(f"[{c}]" for c in COL_NAMES)
    insert_vals  = ", ".join(f"S.[{c}]" for c in COL_NAMES)
    placeholders = ", ".join("?" * len(COL_NAMES))
    on_clause    = " AND ".join(f"T.[{k}] = S.[{k}]" for k in MERGE_KEYS)

    merge_sql = f"""
MERGE [{DST_SCHEMA}].[{table_name}] AS T
USING (VALUES ({placeholders})) AS S ({insert_cols})
ON {on_clause}
WHEN MATCHED THEN
    UPDATE SET {update_set}
WHEN NOT MATCHED BY TARGET THEN
    INSERT ({insert_cols}) VALUES ({insert_vals});
"""
    key_indices = {k: COL_NAMES.index(k) for k in MERGE_KEYS}
    processed = skipped = errors = 0

    for row in rows:
        values = [None if (v is None or str(v).strip().upper() == "NULL") else v for v in row]

        # Skip jika salah satu composite key NULL
        if any(values[idx] is None for idx in key_indices.values()):
            skipped += 1
            log.warning(f"[upsert] Baris di-skip karena composite key NULL: {row}")
            continue

        try:
            cursor.execute(merge_sql, values)
            processed += 1
        except pyodbc.Error as e:
            errors += 1
            log.error(f"[upsert] Gagal pada DeviceID={row[0]}, ProcessorID={row[2]}: {e}")

    cursor.connection.commit()
    log.info(f"[upsert] Selesai. Diproses={processed}, Diskip={skipped}, Error={errors}.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info(f"START sync_processor — {datetime.now()}")
    log.info("=" * 60)

    src_conn = dst_conn = None
    try:
        log.info(f"Menghubungkan ke {SRC_DB} sebagai {SRC_USER}...")
        src_conn = get_connection(SRC_DB, SRC_USER, SRC_PASS)
        src_cur  = src_conn.cursor()

        log.info(f"Menghubungkan ke {DST_DB} sebagai {DST_USER}...")
        dst_conn = get_connection(DST_DB, DST_USER, DST_PASS)
        dst_cur  = dst_conn.cursor()

        ensure_table_exists(dst_cur, SCHEMA["dest_table"])
        rows = fetch_source_data(src_cur, SCHEMA["source_table"])
        upsert_rows(dst_cur, SCHEMA["dest_table"], rows)

    except Exception as e:
        log.exception(f"[FATAL] Sync gagal: {e}")
        sys.exit(1)
    finally:
        if src_conn:
            src_conn.close()
        if dst_conn:
            dst_conn.close()

    log.info(f"FINISH sync_processor — {datetime.now()}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
