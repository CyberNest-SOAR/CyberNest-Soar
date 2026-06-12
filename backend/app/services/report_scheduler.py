"""
report_scheduler.py — Background scheduler for automated report generation.

Uses APScheduler with in-memory job store for initial implementation.
Can be upgraded to PostgreSQL job store for production.

Schedule configuration is stored in JSON file (can be migrated to PostgreSQL).
"""

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.schemas.report_models import ReportType, ReportFormat

logger = logging.getLogger(__name__)

SCHEDULE_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "report_schedules.json"


class ReportScheduler:
    """Manages report schedule CRUD and triggers generation."""

    def __init__(self):
        self._schedules = []
        self._load()

    def _load(self):
        if SCHEDULE_DB_PATH.exists():
            try:
                self._schedules = json.loads(SCHEDULE_DB_PATH.read_text())
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Failed to load schedules: {e}")
                self._schedules = []
        else:
            self._schedules = []
            self._save()

    def _save(self):
        SCHEDULE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCHEDULE_DB_PATH.write_text(json.dumps(self._schedules, indent=2, default=str))

    def list_schedules(self) -> list[dict]:
        return self._schedules

    def get_schedule(self, schedule_id: str) -> dict | None:
        for s in self._schedules:
            if s.get("id") == schedule_id:
                return s
        return None

    def create_schedule(self, schedule: dict) -> dict:
        schedule["id"] = str(uuid.uuid4())
        schedule["created_at"] = datetime.now(timezone.utc).isoformat()
        schedule["last_run_at"] = None
        schedule["next_run_at"] = self._compute_next_run(schedule.get("cron_expression", "0 6 * * *"))
        self._schedules.append(schedule)
        self._save()
        return schedule

    def update_schedule(self, schedule_id: str, updates: dict) -> dict | None:
        for i, s in enumerate(self._schedules):
            if s.get("id") == schedule_id:
                self._schedules[i].update(updates)
                if "cron_expression" in updates:
                    self._schedules[i]["next_run_at"] = self._compute_next_run(updates["cron_expression"])
                self._schedules[i]["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save()
                return self._schedules[i]
        return None

    def delete_schedule(self, schedule_id: str) -> bool:
        for i, s in enumerate(self._schedules):
            if s.get("id") == schedule_id:
                self._schedules.pop(i)
                self._save()
                return True
        return False

    def get_due_schedules(self) -> list[dict]:
        """Get schedules that are due for execution."""
        now = datetime.now(timezone.utc)
        due = []
        for s in self._schedules:
            if not s.get("enabled", True):
                continue
            next_run = s.get("next_run_at")
            if next_run:
                try:
                    if isinstance(next_run, str):
                        next_run_dt = datetime.fromisoformat(next_run)
                    else:
                        next_run_dt = next_run
                    if next_run_dt <= now:
                        due.append(s)
                except (ValueError, TypeError):
                    continue
        return due

    def mark_run_completed(self, schedule_id: str):
        now = datetime.now(timezone.utc)
        for s in self._schedules:
            if s.get("id") == schedule_id:
                s["last_run_at"] = now.isoformat()
                s["next_run_at"] = self._compute_next_run(s.get("cron_expression", "0 6 * * *"))
                self._save()
                break

    def _compute_next_run(self, cron_expr: str) -> str:
        """Simple cron parser for common patterns.
        
        Supports: '0 6 * * *' (daily 6AM), '0 */6 * * *' (every 6h),
        '0 0 * * 1' (weekly Monday), '*/30 * * * *' (every 30 min)
        """
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

        now = datetime.now(timezone.utc)
        minute, hour = parts[0], parts[1]

        if minute == "0" and hour != "*":
            try:
                next_run = now.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run.isoformat()
            except ValueError:
                pass
        elif minute == "0" and hour == "*/6":
            next_hour = ((now.hour // 6) + 1) * 6
            next_run = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
            if next_hour >= 24:
                next_run += timedelta(days=1)
            return next_run.isoformat()
        elif minute == "*/30":
            if now.minute < 30:
                next_run = now.replace(minute=30, second=0, microsecond=0)
            else:
                next_run = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            return next_run.isoformat()

        return (now + timedelta(hours=24)).isoformat()
