import json
import os
from typing import Optional
from ..models.user_settings import UserAISettings


class UserSettingsService:
    def __init__(self, file_path="uploads/user_settings.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                json.dump({}, f)

    def get_settings(self, user_id: str) -> Optional[UserAISettings]:
        with open(self.file_path, "r") as f:
            data = json.load(f)

        if user_id not in data:
            return None

        return UserAISettings(**data[user_id])

    def save_settings(self, settings: UserAISettings):
        with open(self.file_path, "r") as f:
            data = json.load(f)

        data[settings.user_id] = settings.dict()

        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)