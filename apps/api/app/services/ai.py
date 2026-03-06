import httpx
from app.core.config import get_settings

MODELS = {
    "reasoning": "deepseek/deepseek-r1",
    "rag": "google/gemini-2.5-pro",
    "vision": "google/gemini-2.5-pro",
    "report": "anthropic/claude-sonnet-4-6",
    "fallback": "meta-llama/llama-3.3-70b-instruct",
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def call_llm(
    messages: list[dict],
    task: str = "reasoning",
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> str:
    """Call OpenRouter with task-appropriate model."""
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured")
    model = MODELS.get(task, MODELS["fallback"])
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "https://engbrain.app",
        "X-Title": "EngBrain",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def call_vision_llm(image_base64: str, prompt: str, mime_type: str = "image/jpeg") -> str:
    """Call vision-capable model with image."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    return await call_llm(messages, task="vision", max_tokens=4096)
