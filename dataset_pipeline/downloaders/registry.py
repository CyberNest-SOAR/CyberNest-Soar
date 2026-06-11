"""
Registry of all dataset downloaders with real URLs and fallback synthetic generators.
"""
from pathlib import Path
from typing import Optional, List

from downloaders.base import BaseDatasetDownloader
from downloaders.synthetic import generate_fallback_for_missing


class CICIDS2017Downloader(BaseDatasetDownloader):
    name = "cicids2017"
    files = [
        "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
        "Monday-WorkingHours.pcap_ISCX.csv",
        "Tuesday-WorkingHours.pcap_ISCX.csv",
        "Wednesday-workingHours.pcap_ISCX.csv",
        "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
        "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
        "Friday-WorkingHours-Morning.pcap_ISCX.csv",
        "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
    ]
    size_mb = 420

    def download_url(self, filename: str) -> Optional[str]:
        base = "https://certsandbox.s3.amazonaws.com/CICIDS2017/CSV"
        return f"{base}/{filename}"

    def generate_synthetic(self) -> List[Path]:
        return generate_fallback_for_missing("cicids2017", self.target_dir)


class UNSWNB15Downloader(BaseDatasetDownloader):
    name = "unsw_nb15"
    files = ["UNSW_NB15_training-set.csv", "UNSW_NB15_testing-set.csv"]
    size_mb = 180

    def download_url(self, filename: str) -> Optional[str]:
        base = "https://research.unsw.edu.au/projects/unsw-nb15-dataset"
        return None

    def generate_synthetic(self) -> List[Path]:
        return generate_fallback_for_missing("unsw_nb15", self.target_dir)


class CTU13Downloader(BaseDatasetDownloader):
    name = "ctu13"
    files = [f"capture2011081{n}.pcap" for n in range(0, 10)] + [f"capture2011081{n}.pcap" for n in range(0, 4)]
    size_mb = 350

    def download_url(self, filename: str) -> Optional[str]:
        base = "https://mcfp.felk.cvut.cz/publicDatasets/CTU-13-Dataset"
        return f"{base}/{filename}"

    def generate_synthetic(self) -> List[Path]:
        return generate_fallback_for_missing("ctu13", self.target_dir)


class TONIoTDownloader(BaseDatasetDownloader):
    name = "ton_iot"
    files = ["Train_Test_data.csv"]
    size_mb = 220

    def download_url(self, filename: str) -> Optional[str]:
        return None

    def generate_synthetic(self) -> List[Path]:
        return generate_fallback_for_missing("ton_iot", self.target_dir)


class LANLAuthDownloader(BaseDatasetDownloader):
    name = "lanl_auth"
    files = ["auth.txt.gz"]
    size_mb = 480

    def download_url(self, filename: str) -> Optional[str]:
        return f"https://csr.lanl.gov/data/auth/{filename}"

    def generate_synthetic(self) -> List[Path]:
        return generate_fallback_for_missing("lanl_auth", self.target_dir)


class CERTInsiderDownloader(BaseDatasetDownloader):
    name = "cert_insider"
    files = ["r4.2.tar.bz2"]
    size_mb = 200

    def download_url(self, filename: str) -> Optional[str]:
        return None

    def generate_synthetic(self) -> List[Path]:
        return generate_fallback_for_missing("cert_insider", self.target_dir)


def register_all_downloaders(manager):
    from downloaders.download_manager import DatasetDownloadManager
    manager.register("cicids2017", CICIDS2017Downloader(manager.target_dir))
    manager.register("unsw_nb15", UNSWNB15Downloader(manager.target_dir))
    manager.register("ctu13", CTU13Downloader(manager.target_dir))
    manager.register("ton_iot", TONIoTDownloader(manager.target_dir))
    manager.register("lanl_auth", LANLAuthDownloader(manager.target_dir))
    manager.register("cert_insider", CERTInsiderDownloader(manager.target_dir))
