import os
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "https://localhost:9200")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "SecretPassword")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "soc-dataset-4.x")

THEHIVE_URL = os.getenv("THEHIVE_URL", "http://localhost:9000")
THEHIVE_API_KEY = os.getenv("THEHIVE_API_KEY", "")

MAX_DOWNLOAD_SIZE_MB = int(os.getenv("MAX_DOWNLOAD_SIZE_MB", "500"))
PARALLEL_DOWNLOADS = int(os.getenv("PARALLEL_DOWNLOADS", "2"))
TOTAL_EVENTS_TARGET = int(os.getenv("TOTAL_EVENTS_TARGET", "100000"))
REAL_DOWNLOADS_ENABLED = os.getenv("REAL_DOWNLOADS_ENABLED", "true").lower() == "true"
FALLBACK_SYNTHETIC = os.getenv("FALLBACK_SYNTHETIC", "true").lower() == "true"

DATASET_REGISTRY: Dict[str, Dict[str, Any]] = {
    "cicids2017": {
        "url": "https://www.unb.ca/cic/datasets/ids-2017.html",
        "files": [
            "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
            "Monday-WorkingHours.pcap_ISCX.csv",
            "Tuesday-WorkingHours.pcap_ISCX.csv",
            "Wednesday-workingHours.pcap_ISCX.csv",
            "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
            "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
            "Friday-WorkingHours-Morning.pcap_ISCX.csv",
            "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
        ],
        "size_mb": 420,
        "format": "csv",
        "rows_estimate": 2830743,
    },
    "unsw_nb15": {
        "url": "https://research.unsw.edu.au/projects/unsw-nb15-dataset",
        "files": [
            "UNSW_NB15_training-set.csv",
            "UNSW_NB15_testing-set.csv",
        ],
        "size_mb": 180,
        "format": "csv",
        "rows_estimate": 257673,
    },
    "ctu13": {
        "url": "https://stratosphereips.org/category/dataset.html",
        "files": [
            "capture20110810.pcap",
            "capture20110811.pcap",
        ],
        "size_mb": 350,
        "format": "pcap",
        "rows_estimate": 500000,
    },
    "ton_iot": {
        "url": "https://research.unsw.edu.au/projects/toniot-datasets",
        "files": [
            "Train_Test_data.csv",
        ],
        "size_mb": 220,
        "format": "csv",
        "rows_estimate": 400000,
    },
    "lanl_auth": {
        "url": "https://csr.lanl.gov/data/auth/",
        "files": [
            "auth.txt.gz",
        ],
        "size_mb": 480,
        "format": "csv",
        "rows_estimate": 12000000,
    },
    "cert_insider": {
        "url": "https://resources.sei.cmu.edu/library/asset-view.cfm?assetid=508099",
        "files": [
            "r4.2.tar.bz2",
        ],
        "size_mb": 200,
        "format": "csv",
        "rows_estimate": 800000,
    },
}
