from fastapi import APIRouter
from schemas.models import UnifiedAlert, PatchResponse
from services.patch import get_patch_recommendations

router = APIRouter(prefix="/patch", tags=["Team 2: Patch Recommendation"])

@router.post("/", response_model=PatchResponse)
async def recommend_patch_for_alert(alert: UnifiedAlert):
    return await get_patch_recommendations(alert)
