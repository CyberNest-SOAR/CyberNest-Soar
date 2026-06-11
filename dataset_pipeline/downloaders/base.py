import abc
import logging
import requests
from pathlib import Path
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class DownloadProgress:
    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.failed = 0
        self._callbacks: List[Callable] = []

    def on_progress(self, cb: Callable):
        self._callbacks.append(cb)
        return self

    def notify(self, name: str, ok: bool, msg: str = ""):
        if ok:
            self.completed += 1
        else:
            self.failed += 1
        for cb in self._callbacks:
            cb(name, ok, msg, self.completed, self.failed, self.total)


class BaseDatasetDownloader(abc.ABC):
    name: str = ""
    files: List[str] = []
    size_mb: int = 0

    def __init__(self, target_dir: Path, fallback_synthetic: bool = True):
        self.target_dir = target_dir
        self.fallback_synthetic = fallback_synthetic
        self.downloaded: List[Path] = []

    @abc.abstractmethod
    def download_url(self, filename: str) -> Optional[str]:
        ...

    @abc.abstractmethod
    def generate_synthetic(self) -> List[Path]:
        ...

    def verify_file(self, path: Path) -> bool:
        if not path.exists():
            return False
        return path.stat().st_size > 1024

    def download_file(self, filename: str, progress: DownloadProgress) -> Optional[Path]:
        url = self.download_url(filename)
        if not url:
            progress.notify(filename, False, "no URL")
            return None
        dest = self.target_dir / filename
        if dest.exists() and dest.stat().st_size > 1024:
            logger.info("  Already exists: %s (%d MB)", filename, dest.stat().st_size // 1024 // 1024)
            progress.notify(filename, True, "cached")
            self.downloaded.append(dest)
            return dest
        try:
            logger.info("  Downloading %s from %s ...", filename, url)
            r = requests.get(url, stream=True, timeout=300, allow_redirects=True)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192 * 64):
                    f.write(chunk)
                    downloaded += len(chunk)
            if self.verify_file(dest):
                logger.info("  Downloaded %s (%d MB)", filename, dest.stat().st_size // 1024 // 1024)
                progress.notify(filename, True, f"{dest.stat().st_size} bytes")
                self.downloaded.append(dest)
                return dest
            else:
                dest.unlink(missing_ok=True)
                progress.notify(filename, False, "verification failed")
                return None
        except Exception as e:
            logger.warning("  Download failed for %s: %s", filename, e)
            dest.unlink(missing_ok=True)
            progress.notify(filename, False, str(e))
            return None

    def download_all(self, progress: Optional[DownloadProgress] = None) -> List[Path]:
        if not self.files:
            logger.info("No files defined for %s", self.name)
            return self.generate_synthetic()
        prog = progress or DownloadProgress(len(self.files))
        logger.info("Downloading %d files for %s ...", len(self.files), self.name)
        with ThreadPoolExecutor(max_workers=2) as ex:
            futures = {ex.submit(self.download_file, f, prog): f for f in self.files}
            for f in as_completed(futures):
                pass
        if not self.downloaded and self.fallback_synthetic:
            logger.info("Falling back to synthetic data for %s", self.name)
            return self.generate_synthetic()
        return self.downloaded
