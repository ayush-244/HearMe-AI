from pydantic import BaseModel
from typing import Optional


class UserAISettings(BaseModel):
    user_id: str

    # main personalization
    personality_prompt: Optional[str] = None

    # optional presets
    tone: Optional[str] = "balanced"  # friendly, professional, concise, teacher
    style: Optional[str] = "balanced"  # short, balanced, detailed

    created_at: Optional[str] = None
    updated_at: Optional[str] = None