"""
routers/reports.py — Report generation and export API endpoints.

Endpoints:
  GET /reports/executive
  GET /reports/soc-operations
  GET /reports/incidents/{incident_id}
  GET /reports/threat-intel
  GET /reports/hygiene
  GET /reports/shift-handover
  GET /reports/export/{report_type}/{format}
  POST /reports/schedules
  GET /reports/schedules
  DELETE /reports/schedules/{schedule_id}
  POST /reports/schedules/{schedule_id}/test
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from services.report_generator import ReportGenerator
from services.export_service import ExportService, EXPORT_DIR
from services.report_scheduler import ReportScheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])

generator = ReportGenerator()
export_service = ExportService()
scheduler = ReportScheduler()


def _parse_period(period_start: str, period_end: str) -> tuple[datetime, datetime]:
    """Parse period strings, supporting relative formats (7d, 30d, 1d)."""
    now = datetime.now(timezone.utc)

    if period_start.endswith("d"):
        days = int(period_start[:-1])
        start = now - timedelta(days=days)
    else:
        try:
            start = datetime.fromisoformat(period_start)
        except (ValueError, TypeError):
            start = now - timedelta(days=7)

    if period_end == "now" or not period_end:
        end = now
    elif period_end.endswith("d"):
        days = int(period_end[:-1])
        end = now - timedelta(days=days)
    else:
        try:
            end = datetime.fromisoformat(period_end)
        except (ValueError, TypeError):
            end = now

    return start, end


@router.get("/executive")
async def executive_report(
    period_start: str = Query("7d", description="ISO date or relative (30d, 7d, 1d)"),
    period_end: str = Query("now", description="ISO date or 'now'"),
):
    """Generate Executive Security Report for CISO / SOC Director."""
    start, end = _parse_period(period_start, period_end)
    return await generator.generate_executive_report(start, end)


@router.get("/soc-operations")
async def soc_operations_report(
    period_start: str = Query("7d"),
    period_end: str = Query("now"),
):
    """Generate SOC Operations Report for SOC Managers."""
    start, end = _parse_period(period_start, period_end)
    return await generator.generate_soc_operations_report(start, end)


@router.get("/incidents/{incident_id}")
async def incident_report(incident_id: str):
    """Generate Incident Intelligence Report for responders."""
    return await generator.generate_incident_report(incident_id)


@router.get("/threat-intel")
async def threat_intel_report(
    period_start: str = Query("7d"),
    period_end: str = Query("now"),
):
    """Generate Threat Intelligence Report for threat hunters."""
    start, end = _parse_period(period_start, period_end)
    return await generator.generate_threat_intel_report(start, end)


@router.get("/hygiene")
async def hygiene_report(
    period_start: str = Query("30d"),
    period_end: str = Query("now"),
):
    """Generate IT Hygiene Report for security engineering."""
    start, end = _parse_period(period_start, period_end)
    return await generator.generate_hygiene_report(start, end)


@router.get("/shift-handover")
async def shift_handover_report(
    shift_start: str = Query(..., description="Start of shift ISO date"),
    shift_end: str = Query(..., description="End of shift ISO date"),
):
    """Generate Shift Handover Report for SOC analysts."""
    try:
        start = datetime.fromisoformat(shift_start)
        end = datetime.fromisoformat(shift_end)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid shift dates. Use ISO format.")
    return await generator.generate_shift_handover(start, end)


@router.get("/export/{report_type}/{format}")
async def export_report(
    report_type: str,
    format: str,
    period_start: str = Query("7d"),
    period_end: str = Query("now"),
    incident_id: Optional[str] = Query(None),
):
    """Generate and download a report in the specified format.

    Supported report types: executive, soc-operations, incidents, threat-intel, hygiene, shift-handover
    Supported formats: pdf, csv, json, xlsx

    For incident reports, provide incident_id instead of period.
    """
    valid_types = {"executive", "soc-operations", "incidents", "threat-intel", "hygiene", "shift-handover"}
    if report_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid report type: {report_type}. Valid: {valid_types}")

    valid_formats = {"pdf", "csv", "json", "xlsx"}
    if format not in valid_formats:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format}. Valid: {valid_formats}")

    start, end = _parse_period(period_start, period_end)

    # Map report type to generator method name
    type_map = {
        "executive": "executive",
        "soc-operations": "soc_operations",
        "incidents": "incident",
        "threat-intel": "threat_intel",
        "hygiene": "hygiene",
        "shift-handover": "shift_handover",
    }

    # Generate the structured report
    api_type = type_map[report_type]
    if api_type == "incident":
        report = await generator.generate_incident_report(incident_id or "unknown")
    else:
        report = await generator.generate(api_type, start, end, incident_id or "")

    # Export to requested format
    try:
        result = await export_service.export(report, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return FileResponse(
        path=result.path,
        media_type=result.mime_type,
        filename=result.filename,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
            "X-Report-ID": report.get("report_id", ""),
        },
    )


# ── Schedule Management ──

@router.post("/schedules")
async def create_schedule(schedule: dict):
    """Create a new report schedule."""
    return scheduler.create_schedule(schedule)


@router.get("/schedules")
async def list_schedules():
    """List all report schedules."""
    return scheduler.list_schedules()


@router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: str):
    """Get a specific schedule."""
    sched = scheduler.get_schedule(schedule_id)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return sched


@router.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, updates: dict):
    """Update a report schedule."""
    result = scheduler.update_schedule(schedule_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return result


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a report schedule."""
    if not scheduler.delete_schedule(schedule_id):
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted"}


@router.post("/schedules/{schedule_id}/test")
async def test_schedule(schedule_id: str):
    """Immediately generate a report for testing purposes."""
    sched = scheduler.get_schedule(schedule_id)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")

    start, end = _parse_period("7d", "now")

    api_type = sched.get("report_type", "executive")
    report = await generator.generate(api_type, start, end)
    fmt = sched.get("format", "pdf")

    try:
        result = await export_service.export(report, fmt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    scheduler.mark_run_completed(schedule_id)

    return FileResponse(
        path=result.path,
        media_type=result.mime_type,
        filename=result.filename,
    )
