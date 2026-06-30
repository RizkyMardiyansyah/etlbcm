# =============================================================================
# check_columns.py
# Diagnostik: tampilkan daftar kolom asli sebuah tabel/view di source MSSQL.
# Pakai ini kalau ragu dengan nama kolom sebelum menambahkannya ke config.py.
#
# Cara pakai:
#   py check_columns.py V_DeviceTotal_Summary
# =============================================================================

import sys
from config import SRC_SCHEMA
from db_utils import get_src_connection


def main():
    if len(sys.argv) < 2:
        print("Usage: py check_columns.py <nama_tabel_atau_view>")
        sys.exit(1)

    table_name = sys.argv[1]

    conn = get_src_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
               NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, (SRC_SCHEMA, table_name))

    rows = cur.fetchall()
    if not rows:
        print(f"Tidak ditemukan kolom untuk '{SRC_SCHEMA}.{table_name}'.")
        print("Cek apakah nama tabel/view dan schema sudah benar.")
        conn.close()
        sys.exit(1)

    print(f"\nKolom pada {SRC_SCHEMA}.{table_name}:\n")
    print(f"  {'COLUMN_NAME':<30} {'DATA_TYPE':<15} {'LENGTH':<8} {'PREC':<6} {'SCALE':<6} {'NULLABLE'}")
    print(f"  {'-'*30} {'-'*15} {'-'*8} {'-'*6} {'-'*6} {'-'*8}")
    for col, dtype, length, prec, scale, nullable in rows:
        length_str = str(length) if length is not None else "-"
        prec_str   = str(prec) if prec is not None else "-"
        scale_str  = str(scale) if scale is not None else "-"
        print(f"  {col:<30} {dtype:<15} {length_str:<8} {prec_str:<6} {scale_str:<6} {nullable}")

    print(f"\nTotal: {len(rows)} kolom.\n")

    # Cetak juga dalam format Python tuple siap-pakai untuk config.py
    print("--- Format untuk config.py (perlu disesuaikan tipe NVARCHAR/INT manual jika perlu) ---\n")
    for col, dtype, length, prec, scale, nullable in rows:
        if dtype in ("nvarchar", "varchar", "nchar", "char"):
            length_disp = "MAX" if length == -1 else (length or 255)
            mssql_type = f"NVARCHAR({length_disp})"
        elif dtype in ("decimal", "numeric"):
            mssql_type = f"DECIMAL({prec},{scale})"
        elif dtype == "datetime":
            mssql_type = "DATETIME"
        elif dtype == "int":
            mssql_type = "INT"
        elif dtype == "bigint":
            mssql_type = "BIGINT"
        elif dtype == "bit":
            mssql_type = "BIT"
        else:
            mssql_type = dtype.upper()
        print(f'            ("{col}",{" " * max(1, 26 - len(col))}"{mssql_type}"),')

    conn.close()


if __name__ == "__main__":
    main()
