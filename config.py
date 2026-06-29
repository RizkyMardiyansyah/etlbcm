# =============================================================================
# config.py - Konfigurasi koneksi database dan skema tabel
# Digunakan bersama oleh semua script sync bcmdb -> GRAFANADB
# =============================================================================

# ─── Koneksi Database ────────────────────────────────────────────────────────

DB_HOST     = "172.168.3.179"
DB_PORT     = 1434          # SQL Server default port

# Source: bcmdb (baca dengan user sa)
SRC_DB      = "bcmdb"
SRC_USER    = "sa"
SRC_PASS    = "P@ssw0rd2021"

# Destination: GRAFANADB (tulis dengan user grafanauser)
# Destination PostgreSQL
DST_HOST = "172.168.2.120"
DST_PORT = 5432
DST_DB   = "GRAFANADB"
DST_USER = "postgres"
DST_PASS = "P@ssw0rd2021"

DST_SCHEMA = "public"

# ─── Driver ODBC ─────────────────────────────────────────────────────────────
ODBC_DRIVER = "ODBC Driver 17 for SQL Server"

# ─── Schema Database ──────────────────────────────────────────────────────────
# Query ke bcmdb: [bcmdbuser].[NamaTabel]
SRC_SCHEMA  = "bcmdbuser"
# Tabel tujuan di GRAFANADB: [dbo].[NamaTabel]
# DST_SCHEMA  = "dbo"

# ─── Skema Tabel ─────────────────────────────────────────────────────────────

TABLE_SCHEMAS = {

    # ── Atrium_CMDB_ComputerSystem ────────────────────────────────────────────
    "Atrium_CMDB_ComputerSystem": {
        "source_table" : "Atrium_CMDB_ComputerSystem",
        "dest_table"   : "Atrium_CMDB_ComputerSystem",
        "primary_key"  : "DeviceID",
        "columns": [
            ("DeviceID",              "INT"),
            ("DeviceName",            "NVARCHAR(255)"),
            ("OperatingSystemName",   "NVARCHAR(512)"),
            ("SerialNumber",          "NVARCHAR(255)"),
            ("Description",           "NVARCHAR(512)"),
            ("ShortDescription",      "NVARCHAR(512)"),
            ("DeviceType",            "NVARCHAR(128)"),
            ("TopologyType",          "NVARCHAR(128)"),
            ("LastUpdate",            "DATETIME"),
            ("VirtualSystemType",     "NVARCHAR(128)"),
            ("IsVirtual",             "NVARCHAR(10)"),
            ("TokenID",               "NVARCHAR(255)"),
            ("ManufacturerName",      "NVARCHAR(255)"),
            ("ModelName",             "NVARCHAR(255)"),
            ("Domain",                "NVARCHAR(255)"),
            ("HostName",              "NVARCHAR(255)"),
            ("PhysicalMemory",        "NVARCHAR(128)"),
            ("AssetTag",              "NVARCHAR(255)"),
            ("Location",              "NVARCHAR(255)"),
            ("PrimaryUserLogin",      "NVARCHAR(255)"),
            ("PrimaryUserDomain",     "NVARCHAR(255)"),
            ("LastLoggedInUser",      "NVARCHAR(255)"),
        ],
    },

    # ── Atrium_CMDB_NetworkInterface ─────────────────────────────────────────
    "Atrium_CMDB_NetworkInterface": {
        "source_table" : "Atrium_CMDB_NetworkInterface",
        "dest_table"   : "Atrium_CMDB_NetworkInterface",
        "primary_key"  : None,
        "merge_keys"   : ["DeviceID", "NetworkInterfaceID"],
        "columns": [
            ("DeviceID",              "INT"),
            ("DeviceName",            "NVARCHAR(255)"),
            ("LastUpdate",            "DATETIME"),
            ("NetworkInterfaceID",    "NVARCHAR(64)"),
            ("MACAddress",            "NVARCHAR(64)"),
            ("IPAddress",             "NVARCHAR(64)"),
            ("Name",                  "NVARCHAR(255)"),
            ("ShortDescription",      "NVARCHAR(512)"),
            ("Description",           "NVARCHAR(512)"),
        ],
    },

    # ── Atrium_CMDB_OperatingSystem ──────────────────────────────────────────
    "Atrium_CMDB_OperatingSystem": {
        "source_table" : "Atrium_CMDB_OperatingSystem",
        "dest_table"   : "Atrium_CMDB_OperatingSystem",
        "primary_key"  : "InventoryID",
        "columns": [
            ("DeviceID",              "INT"),
            ("InventoryID",           "NVARCHAR(64)"),
            ("DeviceName",            "NVARCHAR(255)"),
            ("BuildNumber",           "NVARCHAR(64)"),
            ("ServicePack",           "NVARCHAR(64)"),
            ("VersionNumber",         "NVARCHAR(64)"),
            ("Description",           "NVARCHAR(512)"),
            ("OSName",                "NVARCHAR(512)"),
            ("OSLanguage",            "NVARCHAR(128)"),
            ("ShortDescription",      "NVARCHAR(512)"),
            ("LastUpdate",            "DATETIME"),
        ],
    },

    # ── Atrium_CMDB_Processor ────────────────────────────────────────────────
    "Atrium_CMDB_Processor": {
        "source_table" : "Atrium_CMDB_Processor",
        "dest_table"   : "Atrium_CMDB_Processor",
        "primary_key"  : None,
        "merge_keys"   : ["DeviceID", "InstanceName"],
        "columns": [
            ("DeviceID",                    "INT"),
            ("DeviceName",                  "NVARCHAR(255)"),
            ("InstanceName",                "NVARCHAR(255)"),
            ("NumberOfLogicalProcessors",   "INT"),
            ("InventoryID",                 "NVARCHAR(64)"),
            ("ProcessorFamily",             "NVARCHAR(255)"),
            ("Description",                 "NVARCHAR(512)"),
            ("ShortDescription",            "NVARCHAR(512)"),
            ("Name",                        "NVARCHAR(255)"),
            ("ManufacturerName",            "NVARCHAR(255)"),
            ("MaxClockSpeed",               "INT"),
            ("LastUpdate",                  "DATETIME"),
        ],
    },

    # ── Atrium_CMDB_Software ─────────────────────────────────────────────────
    "Atrium_CMDB_Software": {
        "source_table" : "Atrium_CMDB_Software",
        "dest_table"   : "Atrium_CMDB_Software",
        "primary_key"  : None,
        "merge_keys"   : ["DeviceID", "InventoryID"],
        "columns": [
            ("DeviceID",              "INT"),
            ("InventoryID",           "NVARCHAR(64)"),
            ("ManufacturerName",      "NVARCHAR(255)"),
            ("Name",                  "NVARCHAR(512)"),
            ("VersionNumber",         "NVARCHAR(128)"),
            ("Model",                 "NVARCHAR(255)"),
            ("MarketVersion",         "NVARCHAR(128)"),
            ("Status",                "NVARCHAR(128)"),
            ("IntegrationDate",       "DATETIME"),
            ("CategoryName",          "NVARCHAR(255)"),
        ],
    },

    # ── FAMView ───────────────────────────────────────────────────────────────
    "FAMView": {
        "source_table" : "FAMView",
        "dest_table"   : "FAMView",
        "primary_key"  : "DeviceID",
        "columns": [
            ("DeviceID",              "INT"),
            ("AdministratorID",       "NVARCHAR(255)"),
            ("AssetAdmin",            "NVARCHAR(255)"),
            ("UserID",                "NVARCHAR(255)"),
            ("AssetUser",             "NVARCHAR(255)"),
            ("GroupID",               "NVARCHAR(255)"),
            ("Department",            "NVARCHAR(255)"),
            ("VendorID",              "NVARCHAR(255)"),
            ("VendorName",            "NVARCHAR(255)"),
            ("VendorSKU",             "NVARCHAR(255)"),
            ("PONumber",              "NVARCHAR(255)"),
            ("SProvider",             "NVARCHAR(255)"),
            ("LifeCycleStatus",       "NVARCHAR(128)"),
            ("PrimaryUser",           "NVARCHAR(255)"),
        ],
    },

    # ── V_CMDB_FAM ───────────────────────────────────────────────────────────
    # 31 kolom sesuai header yang dikonfirmasi user
    "V_CMDB_FAM": {
        "source_table" : "V_CMDB_FAM",
        "dest_table"   : "V_CMDB_FAM",
        "primary_key"  : "DeviceID",
        "columns": [
            ("DeviceID",              "INT"),
            ("AssetAdmin",            "NVARCHAR(255)"),
            ("AssetUser",             "NVARCHAR(255)"),
            ("Department",            "NVARCHAR(255)"),
            ("FAMLocation",           "NVARCHAR(255)"),
            ("VendorName",            "NVARCHAR(255)"),
            ("VendorSKU",             "NVARCHAR(255)"),
            ("PONumber",              "NVARCHAR(255)"),
            ("SProvider",             "NVARCHAR(255)"),
            ("LifeCycleStatus",       "NVARCHAR(128)"),
            ("PrimaryUser",           "NVARCHAR(255)"),
            ("AssetTag",              "NVARCHAR(255)"),
            ("InvoiceNumber",         "NVARCHAR(255)"),
            ("WETime",                "NVARCHAR(255)"),
            ("WCost",                 "DECIMAL(18,4)"),
            ("STime",                 "NVARCHAR(255)"),
            ("SCost",                 "DECIMAL(18,4)"),
            ("SPhone",                "NVARCHAR(255)"),
            ("PTime",                 "DATETIME"),
            ("InvoiceDate",           "DATETIME"),
            ("RTime",                 "DATETIME"),
            ("SSTime",                "DATETIME"),
            ("PCost",                 "DECIMAL(18,4)"),
            ("Residual",              "DECIMAL(18,4)"),
            ("UsefulLife",            "INT"),
            ("LCost",                 "DECIMAL(18,4)"),
            ("LTermNumber",           "NVARCHAR(255)"),
            ("IsPurchased",           "INT"),
            ("DepreciationType",      "NVARCHAR(128)"),
            ("GCost",                 "DECIMAL(18,4)"),
            ("ACost",                 "DECIMAL(18,4)"),
        ],
    },

    # ── V_CMDB_Device ────────────────────────────────────────────────────────
    "V_CMDB_Device": {
        "source_table" : "V_CMDB_Device",
        "dest_table"   : "V_CMDB_Device",
        "primary_key"  : "DeviceID",
        "columns": [
            ("DeviceID",              "INT"),
            ("DeviceName",            "NVARCHAR(255)"),
            ("LastAudit",             "DATETIME"),
            ("IPAddress",             "NVARCHAR(64)"),
            ("MACAddress",            "NVARCHAR(64)"),
            ("OperatingSystemName",   "NVARCHAR(512)"),
            ("VIMMachineVendor",      "NVARCHAR(255)"),
            ("HypervisorVendor",      "NVARCHAR(255)"),
            ("Manufacturer",          "NVARCHAR(255)"),
            ("Model",                 "NVARCHAR(255)"),
            ("Notes",                 "NVARCHAR(1024)"),
            ("SerialNumber",          "NVARCHAR(255)"),
            ("LastLoggedInUser",      "NVARCHAR(255)"),
            ("DeviceType",            "NVARCHAR(128)"),
            ("Status",                "NVARCHAR(64)"),
            ("Memory",                "NVARCHAR(512)"),
            ("DiskDrives",            "NVARCHAR(1024)"),
            ("ProcessorDetails",      "NVARCHAR(512)"),
            ("DrivePartitions",       "NVARCHAR(1024)"),
            ("LastRIScanDate",        "DATETIME"),
            ("DiscoveredBy",          "NVARCHAR(255)"),
        ],
    },

    # ── V_CMDB_Software ──────────────────────────────────────────────────────
    "V_CMDB_Software": {
        "source_table" : "V_CMDB_Software",
        "dest_table"   : "V_CMDB_Software",
        "primary_key"  : None,
        "merge_keys"   : ["Name", "Version"],
        "columns": [
            ("Name",                  "NVARCHAR(512)"),
            ("Version",               "NVARCHAR(128)"),
            ("Manufacturer",          "NVARCHAR(255)"),
            ("Type",                  "NVARCHAR(128)"),
            ("CopiesInstalled",       "INT"),
            ("CopiesInUse",           "INT"),
        ],
    },

    # ── V_CMDB_SoftwareRel ───────────────────────────────────────────────────
    "V_CMDB_SoftwareRel": {
        "source_table" : "V_CMDB_SoftwareRel",
        "dest_table"   : "V_CMDB_SoftwareRel",
        "primary_key"  : None,
        "merge_keys"   : ["DeviceID", "Name", "Version"],
        "columns": [
            ("DeviceID",              "INT"),
            ("OperatingSystemName",   "NVARCHAR(512)"),
            ("Name",                  "NVARCHAR(512)"),
            ("Version",               "NVARCHAR(128)"),
            ("Manufacturer",          "NVARCHAR(255)"),
            ("InstallDirectory",      "NVARCHAR(1024)"),
        ],
    },
}
