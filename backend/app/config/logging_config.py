"""Centralized logging configuration for the SOAR backend.

This module exposes `configure_logging()` which sets up a console
handler and a rotating file handler under `backend/logs/soar.log`.

Call `configure_logging()` very early (before other modules log).
"""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Dict


LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "soar.log"


def _ensure_log_dir() -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fall back silently; handlers will raise if files cannot be created
        pass


def configure_logging(level: str | int = logging.INFO) -> None:
    """Configure root logging for the application.

    - Creates `backend/logs/soar.log` (Rotating) and a console handler.
    - Intended to be idempotent and safe to call multiple times.
    """
    _ensure_log_dir()

    root = logging.getLogger()
    # Avoid double configuration
    if getattr(root, "__soar_configured__", False):
        return

    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(fmt)
    root.addHandler(console)

    try:
        rotating = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        rotating.setLevel(level)
        rotating.setFormatter(fmt)
        root.addHandler(rotating)
    except Exception:
        # If file handler can't be created (permissions, read-only FS), continue
        root.warning("Could not create file handler for logging; continuing with console only")

    # mark configured so repeated calls are no-ops
    setattr(root, "__soar_configured__", True)


def get_log_file_path() -> Path:
    return LOG_FILE
