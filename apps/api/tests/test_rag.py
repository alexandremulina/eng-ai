import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.rag import query_norms, search_norm_documents, get_embedding


@pytest.mark.anyio
async def test_query_norms_returns_no_results_message_when_empty():
    with patch("app.services.rag.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 1536), \
         patch("app.services.rag.search_norm_documents", new_callable=AsyncMock, return_value=[]):
        result = await query_norms("What is NPSHr?", "user-123")
    assert result["answer"] == "No relevant norm sections found for this query."
    assert result["citations"] == []


@pytest.mark.anyio
async def test_query_norms_returns_answer_with_citations_when_docs_found():
    mock_docs = [
        {"content": "API 610 section 6.1 states NPSHr...", "metadata": {"source": "API 610", "page": 45}, "similarity": 0.92},
        {"content": "NPSHr values are determined by...", "metadata": {"source": "API 610", "page": 46}, "similarity": 0.87},
    ]
    with patch("app.services.rag.get_embedding", new_callable=AsyncMock, return_value=[0.1] * 1536), \
         patch("app.services.rag.search_norm_documents", new_callable=AsyncMock, return_value=mock_docs), \
         patch("app.services.rag.call_llm", new_callable=AsyncMock, return_value="NPSHr as per API 610 section 6.1..."):
        result = await query_norms("What is NPSHr?", "user-123")
    assert "NPSHr" in result["answer"]
    assert len(result["citations"]) == 2
    assert result["citations"][0]["source"] == "API 610"
    assert result["citations"][0]["page"] == 45


@pytest.mark.anyio
async def test_get_embedding_calls_openrouter():
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
    with patch("app.services.rag.get_openrouter_embeddings_client") as mock_client_fn:
        mock_client = AsyncMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_client_fn.return_value = mock_client
        result = await get_embedding("test query")
    assert len(result) == 1536
    mock_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input="test query",
    )


@pytest.mark.anyio
async def test_query_norms_endpoint_requires_auth():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/norms/query", json={"question": "What is NPSHr?"})
    assert response.status_code in (401, 403)


@pytest.mark.anyio
async def test_query_norms_endpoint_returns_answer(mock_user):
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    with patch("app.routers.norms.query_norms", new_callable=AsyncMock, return_value={
        "answer": "NPSHr is ...", "citations": []
    }), patch("app.routers.norms.check_and_record_usage"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/norms/query",
                json={"question": "What is NPSHr?"},
                headers={"Authorization": "Bearer test-token"},
            )
    assert response.status_code == 200
    assert "answer" in response.json()
