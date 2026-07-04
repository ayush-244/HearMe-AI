const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type UserAISettings = {
  user_id: string;
  personality_prompt?: string;
  tone?: string;
  style?: string;
};

// GET settings
export async function getUserSettings(userId: string) {
  const res = await fetch(`${BASE_URL}/api/v1/settings/${userId}`);
  return res.json();
}

// SAVE settings
export async function updateUserSettings(data: UserAISettings) {
  const res = await fetch(`${BASE_URL}/api/v1/settings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return res.json();
}
