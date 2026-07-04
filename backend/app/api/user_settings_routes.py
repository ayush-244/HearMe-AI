from fastapi import APIRouter
from pydantic import BaseModel
from ..services.user_settings_service import UserSettingsService
from ..models.user_settings import UserAISettings

router = APIRouter(prefix="/api/v1/settings", tags=["User Settings"])

service = UserSettingsService()


class SettingsRequest(BaseModel):
    user_id: str
    personality_prompt: str | None = None
    tone: str | None = None
    style: str | None = None


@router.get("/{user_id}")
def get_settings(user_id: str):
    return service.get_settings(user_id) or {}


@router.post("/")
def update_settings(req: SettingsRequest):

    existing = service.get_settings(req.user_id)

    if existing:
        settings = existing
        settings.personality_prompt = req.personality_prompt
        settings.tone = req.tone
        settings.style = req.style
    else:
        settings = UserAISettings(**req.dict())

    service.save_settings(settings)

    return {"status": "ok", "settings": settings}