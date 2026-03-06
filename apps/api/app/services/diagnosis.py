import base64
import json
from app.services.ai import call_vision_llm

DIAGNOSIS_SYSTEM = """You are a pump failure analysis expert trained on ISO 14224 failure taxonomy.
Analyze the provided image of a pump component and return a JSON object with:
{
  "component": "identified component (e.g., mechanical seal, impeller, bearing)",
  "root_cause": "most likely cause of failure or condition",
  "severity": "low | medium | high | critical",
  "confidence": "low | medium | high",
  "immediate_action": "what to do right now",
  "preventive_action": "how to prevent recurrence",
  "possible_causes": ["list", "of", "other", "possible", "causes"],
  "disclaimer": "This is an AI-assisted diagnosis. Always validate with certified inspection."
}
Respond ONLY with valid JSON. No markdown, no extra text."""


async def diagnose_component(image_bytes: bytes, notes: str = "", mime_type: str = "image/jpeg") -> dict:
    """Analyze pump component image for failure diagnosis."""
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = DIAGNOSIS_SYSTEM
    if notes:
        prompt += f"\n\nEngineer notes: {notes}"

    raw = await call_vision_llm(image_b64, prompt, mime_type=mime_type)

    # Strip markdown code blocks if present
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return {
            "component": "Unknown",
            "root_cause": "Could not parse AI response",
            "severity": "unknown",
            "confidence": "low",
            "immediate_action": "Manual inspection required",
            "preventive_action": "N/A",
            "possible_causes": [],
            "disclaimer": "AI diagnosis unavailable. Raw response: " + raw[:200],
        }
