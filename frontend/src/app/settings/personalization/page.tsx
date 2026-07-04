"use client";

import { useEffect, useState } from "react";
import {
  getUserSettings,
  updateUserSettings,
} from "@/lib/api/user-settings";

export default function PersonalizationPage() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const userId = "default"; // replace later with auth user

  useEffect(() => {
    async function load() {
      const data = await getUserSettings(userId);

      if (data?.personality_prompt) {
        setText(data.personality_prompt);
      }
    }

    load();
  }, []);

  const save = async () => {
    setLoading(true);

    await updateUserSettings({
      user_id: userId,
      personality_prompt: text,
      tone: "balanced",
      style: "balanced",
    });

    setLoading(false);
    alert("Saved!");
  };

  return (
    <div className="p-6 max-w-2xl mx-auto text-white">
      <h1 className="text-2xl font-semibold mb-2">
        AI Personalization
      </h1>

      <p className="text-sm text-gray-400 mb-4">
        Customize how HearMe AI responds to you
      </p>

      <div className="flex gap-2 mb-3">
        {["concise", "balanced", "detailed"].map((s) => (
          <button
            key={s}
            onClick={() =>
              setText(`Respond in a ${s} way with clear structure.`)
            }
            className="px-3 py-1 text-xs rounded-full bg-zinc-800 hover:bg-zinc-700 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      <textarea
        className="w-full h-48 p-4 rounded-lg bg-zinc-900 border border-zinc-700"
        placeholder="Example: Explain everything in simple terms with examples..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <button
        onClick={save}
        disabled={loading}
        className="mt-4 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors disabled:opacity-50"
      >
        {loading ? "Saving..." : "Save Preferences"}
      </button>
    </div>
  );
}
