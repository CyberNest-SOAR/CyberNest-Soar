import asyncio
import logging
from fastapi import APIRouter
from typing import List
from schemas.models import UnifiedAlert, PatchResponse
from services.patch import get_patch_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patch", tags=["Team 2: Patch Recommendation"])


@router.post("/", response_model=PatchResponse)
async def recommend_patch_for_alert(alert: UnifiedAlert):
    """Legacy endpoint: POST /patch with UnifiedAlert."""
    return await get_patch_recommendations(alert)


@router.post("/batch", response_model=List[PatchResponse])
async def recommend_patch_batch(alerts: List[UnifiedAlert]):
    """
    Recommend patches for a batch of alerts. Accepts the raw
    ``List[UnifiedAlert]`` array returned by ``GET /alerts/``.
    """
    results = await asyncio.gather(
        *[get_patch_recommendations(a) for a in alerts],
        return_exceptions=True,
    )
    out = []
    for alert, result in zip(alerts, results):
        if isinstance(result, Exception):
            logger.warning("[Patch] Recommendation failed for %s: %s", alert.event_id, result)
            continue
        out.append(result)
    return out
