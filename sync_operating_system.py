# =============================================================================
# sync_operating_system.py
# Sinkronisasi: bcmdb (MSSQL) -> GRAFANADB (PostgreSQL)
# Tabel: Atrium_CMDB_OperatingSystem | PK: InventoryID
# =============================================================================

import logging
import os
import sys
from datetime import datetime

from config import TABLE_SCHEMAS, SRC_SCHEMA, DST_SCHEMA
from db_utils import get_src_connection, get_dst_connection, \
                     ensure_table_exists_pg, fetch_source_data, upsert_rows_pg

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"sync_operating_system_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

TABLE_KEY  = "Atrium_CMDB_OperatingSystem"
SCHEMA     = TABLE_SCHEMAS[TABLE_KEY]
COLUMNS    = SCHEMA["columns"]
COL_NAMES  = [c[0] for c in COLUMNS]
PK         = SCHEMA["primary_key"]
MERGE_KEYS = SCHEMA.get("merge_keys")


def main():
    log.info("=" * 60)
    log.info(f"START sync_operating_system — {datetime.now()}")
    log.info("=" * 60)

    src_conn = dst_conn = None
    try:
        log.info("Menghubungkan ke source MSSQL (bcmdb)...")
        src_conn = get_src_connection()
        src_cur  = src_conn.cursor()

        log.info("Menghubungkan ke destination PostgreSQL (GRAFANADB)...")
        dst_conn = get_dst_connection()

        ensure_table_exists_pg(
            dst_conn, DST_SCHEMA, SCHEMA["dest_table"],
            COLUMNS, PK, MERGE_KEYS, log,
        )
        rows = fetch_source_data(src_cur, SRC_SCHEMA, SCHEMA["source_table"], COL_NAMES, log)
        upsert_rows_pg(dst_conn, DST_SCHEMA, SCHEMA["dest_table"], COL_NAMES, PK, MERGE_KEYS, rows, log)

    except Exception as e:
        log.exception(f"[FATAL] Sync gagal: {e}")
        sys.exit(1)
    finally:
        if src_conn:
            src_conn.close()
        if dst_conn:
            dst_conn.close()

    log.info(f"FINISH sync_operating_system — {datetime.now()}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
