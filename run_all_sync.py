# =============================================================================
# run_all_sync.py
# Master script — menjalankan semua script sync bcmdb -> GRAFANADB secara
# berurutan. Cukup jalankan file ini saja via Task Scheduler Windows.
#
# Urutan eksekusi:
#   1. sync_computer_system.py
#   2. sync_network_interface.py
#   3. sync_operating_system.py
#   4. sync_processor.py
#   5. sync_famview.py
# =============================================================================

import subprocess
import sys
import logging
import os
from datetime import datetime

# ─── Fix encoding untuk Windows console (Python 3.7+) ────────────────────────
# Pastikan stdout/stderr master script sendiri bisa menampilkan UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # fallback jika reconfigure tidak didukung

# ─── Logging ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR  = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"run_all_sync_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ─── Daftar script yang akan dijalankan (urutan penting) ─────────────────────
SCRIPTS = [
    "sync_computer_system.py",    # Atrium_CMDB_ComputerSystem
    "sync_network_interface.py",  # Atrium_CMDB_NetworkInterface
    "sync_operating_system.py",   # Atrium_CMDB_OperatingSystem
    "sync_processor.py",          # Atrium_CMDB_Processor
    "sync_atrium_software.py",    # Atrium_CMDB_Software  (BARU)
    "sync_famview.py",            # FAMView
    "sync_vcmdb_fam.py",          # V_CMDB_FAM
    "sync_device.py",             # V_CMDB_Device
    "sync_software.py",           # V_CMDB_Software
    "sync_software_rel.py",       # V_CMDB_SoftwareRel
    "sync_device_total_summary.py", # V_DeviceTotal_Summary (BARU)
]


# ─── Runner ───────────────────────────────────────────────────────────────────

def run_script(script_name: str) -> bool:
    """
    Jalankan satu script Python sebagai subprocess.
    Return True jika sukses, False jika gagal.
    """
    script_path = os.path.join(BASE_DIR, script_name)

    if not os.path.isfile(script_path):
        log.error(f"[SKIP] File tidak ditemukan: {script_path}")
        return False

    log.info(f"{'─' * 50}")
    log.info(f"▶  Menjalankan: {script_name}")
    log.info(f"{'─' * 50}")

    try:
        # ── Paksa child process juga pakai UTF-8 via env var ──────────────────
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8:replace"   # output child process = UTF-8
        env["PYTHONUTF8"]       = "1"               # aktifkan UTF-8 mode (Python 3.7+)

        # Tangkap output sebagai BYTES (bukan text) untuk menghindari
        # UnicodeDecodeError pada Windows dengan encoding default cp1252.
        result = subprocess.run(
            [sys.executable, "-u", script_path],    # -u = unbuffered output
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=BASE_DIR,
            env=env,
        )

        # Decode bytes ke string, ganti karakter yang tidak dikenal dengan '?'
        stdout_text = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
        stderr_text = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""

        # Tampilkan output script ke log
        if stdout_text.strip():
            for line in stdout_text.strip().splitlines():
                log.info(f"   {line}")
        if stderr_text.strip():
            for line in stderr_text.strip().splitlines():
                log.warning(f"   [STDERR] {line}")

        if result.returncode == 0:
            log.info(f"[OK] {script_name} selesai dengan sukses.")
            return True
        else:
            log.error(f"[GAGAL] {script_name} selesai dengan error (exit code: {result.returncode}).")
            return False

    except Exception as e:
        log.exception(f"[GAGAL] Gagal menjalankan {script_name}: {e}")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    start_time = datetime.now()

    log.info("=" * 60)
    log.info(f"  RUN ALL SYNC — START: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"  Total script: {len(SCRIPTS)}")
    log.info("=" * 60)

    results = {}

    for script in SCRIPTS:
        success = run_script(script)
        results[script] = "[SUKSES]" if success else "[GAGAL] "

    # ── Ringkasan akhir ────────────────────────────────────────────────────
    end_time  = datetime.now()
    duration  = end_time - start_time
    total_ok  = sum(1 for v in results.values() if "SUKSES" in v)
    total_err = len(results) - total_ok

    log.info("")
    log.info("=" * 60)
    log.info("  RINGKASAN EKSEKUSI")
    log.info("=" * 60)
    for script, status in results.items():
        log.info(f"  {status}  -  {script}")
    log.info("-" * 60)
    log.info(f"  Total: {total_ok} sukses, {total_err} gagal")
    log.info(f"  Durasi: {str(duration).split('.')[0]}")
    log.info(f"  Selesai: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    # Exit dengan kode error jika ada script yang gagal
    if total_err > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
