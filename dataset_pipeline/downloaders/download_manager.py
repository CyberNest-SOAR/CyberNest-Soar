import logging
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.settings import RAW_DIR, DATASET_REGISTRY, REAL_DOWNLOADS_ENABLED, FALLBACK_SYNTHETIC
from downloaders.base import BaseDatasetDownloader, DownloadProgress

logger = logging.getLogger(__name__)


class DatasetDownloadManager:
    def __init__(self, target_dir: Path = RAW_DIR):
        self.target_dir = target_dir
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, List[Path]] = {}
        self._downloaders: Dict[str, BaseDatasetDownloader] = {}

    def register(self, name: str, downloader: BaseDatasetDownloader):
        self._downloaders[name] = downloader

    def download_all(self) -> Dict[str, List[Path]]:
        names = list(self._downloaders.keys())
        total = sum(len(self._downloaders[n].files) or 1 for n in names)
        prog = DownloadProgress(total)

        def _log(name: str, ok: bool, msg: str, done: int, failed: int, total_: int):
            logger.info("  [%d/%d] %s: %s %s", done + failed, total_, name, "OK" if ok else "FAIL", msg)

        prog.on_progress(_log)

        with ThreadPoolExecutor(max_workers=2) as ex:
            fut_map = {ex.submit(self._download_one, n, prog): n for n in names}
            for f in as_completed(fut_map):
                name = fut_map[f]
                try:
                    self.results[name] = f.result()
                except Exception as e:
                    logger.error("Downloader %s crashed: %s", name, e)
                    self.results[name] = []

        total_ok = sum(len(v) for v in self.results.values())
        logger.info("Download complete: %d files across %d datasets", total_ok, len(self.results))
        return self.results

    def _download_one(self, name: str, prog: DownloadProgress) -> List[Path]:
        dl = self._downloaders[name]
        return dl.download_all(prog)

    def summary(self) -> str:
        lines = ["Dataset Download Summary", "=" * 50]
        total = 0
        for name, paths in self.results.items():
            count = len(paths)
            real = sum(1 for p in paths if p.suffix != ".json")
            synth = count - real
            size_mb = sum(p.stat().st_size for p in paths if p.exists()) // 1024 // 1024
            lines.append(f"  {name:20s} {count:3d} files ({real} real, {synth} synthetic) {size_mb} MB")
            total += size_mb
        lines.append(f"{'TOTAL':20s} {total} MB")
        return "\n".join(lines)
