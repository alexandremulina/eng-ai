import asyncio
import openai
from app.core.config import get_settings
from app.core.supabase import get_supabase
from app.services.ai import call_llm

NORM_SYSTEM_PROMPT_RAG = """You are a senior pump engineering specialist with deep expertise in:
- API 610 (centrifugal pumps for petroleum industry)
- API 682 (shaft sealing systems)
- ASME B73 (horizontal end-suction pumps)
- ISO 5199 (technical specifications for centrifugal pumps)

Answer the engineer's question using ONLY the provided context from the norm documents.
Always cite: norm name, section number, and page if available.
If the context doesn't contain the answer, say so explicitly — never guess.
Format your response clearly with the citation at the end."""

NORM_SYSTEM_PROMPT_DIRECT = """You are a senior pump & rotating equipment engineer with 25+ years of experience applying:
- API 610 / API 682 / API 685
- ASME B73.1 / B73.2
- ISO 5199 / ISO 13709
- HI Standards (Hydraulic Institute)

Rules:
1. Answer the question directly and thoroughly. Do not ask for clarification — give the best answer based on what was asked.
2. Always include the specific norm, edition, section/clause number when referencing requirements.
3. Use bullet points and short paragraphs for readability.
4. If a requirement has specific numerical values (tolerances, limits, test pressures), include them.
5. If different norms have different requirements for the same topic, compare them.
6. End with a "Key References" section listing the norms and sections cited.
7. If you are not sure about a specific section number, say "refer to" instead of guessing a wrong number."""


def get_openrouter_embeddings_client() -> openai.AsyncOpenAI:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not configured")
    return openai.AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )


async def get_embedding(text: str) -> list[float]:
    """Get text embedding via OpenRouter."""
    client = get_openrouter_embeddings_client()
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


async def search_norm_documents(
    question_embedding: list[float],
    user_id: str,
    match_threshold: float = 0.7,
    match_count: int = 5,
) -> list[dict]:
    """Search Supabase pgvector for relevant norm sections."""
    supabase = get_supabase()

    def _execute():
        return supabase.rpc(
            "match_norm_documents",
            {
                "query_embedding": question_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "filter_user_id": user_id,
            },
        ).execute()

    results = await asyncio.to_thread(_execute)
    return results.data or []


# TODO: re-enable RAG pipeline when pgvector tables are set up
# async def _query_norms_rag(question: str, user_id: str, language: str = "en") -> dict:
#     """RAG query against norm documents (requires pgvector)."""
#     question_embedding = await get_embedding(question)
#     results = await search_norm_documents(question_embedding, user_id)
#     if not results:
#         return {"answer": "No relevant norm sections found for this query.", "citations": []}
#     context_chunks = [r["content"] for r in results]
#     citations = [
#         {"source": r.get("metadata", {}).get("source", "Unknown"),
#          "page": r.get("metadata", {}).get("page"),
#          "similarity": round(r.get("similarity", 0), 3)}
#         for r in results
#     ]
#     context = "\n\n---\n\n".join(context_chunks)
#     messages = [
#         {"role": "system", "content": NORM_SYSTEM_PROMPT},
#         {"role": "user", "content": f"Context from norm documents:\n\n{context}\n\nQuestion: {question}"},
#     ]
#     answer = await call_llm(messages, task="rag", temperature=0.0)
#     return {"answer": answer, "citations": citations}


async def query_norms(question: str, user_id: str, language: str = "en") -> dict:
    """Direct LLM query (no RAG) — temporary until pgvector is ready."""
    lang_instruction = {
        "pt": "Respond in Brazilian Portuguese.",
        "es": "Respond in Spanish.",
        "en": "Respond in English.",
    }.get(language, "")

    messages = [
        {"role": "system", "content": f"{NORM_SYSTEM_PROMPT_DIRECT}\n\n{lang_instruction}"},
        {"role": "user", "content": question},
    ]
    answer = await call_llm(messages, task="rag", temperature=0.0)
    return {"answer": answer, "citations": []}
