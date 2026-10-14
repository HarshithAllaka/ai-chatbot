from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.embedding_service import EmbeddingService


@pytest.mark.asyncio
async def test_generate_embeddings_cache_miss_and_hit():
    service = EmbeddingService()
    
    # Mock Gemini client
    mock_emb_1 = MagicMock()
    mock_emb_1.values = [0.1, 0.2, 0.3]
    mock_response = MagicMock()
    mock_response.embeddings = [mock_emb_1]
    
    service.client = MagicMock()
    service.client.aio.models.embed_content = AsyncMock(return_value=mock_response)
    
    # Mock Redis client
    mock_redis = MagicMock()
    mock_redis.mget = AsyncMock(return_value=[None])  # Cache miss first time
    
    # Mock pipeline
    mock_pipe = AsyncMock()
    mock_pipe.setex = MagicMock()
    mock_pipe.execute = AsyncMock()
    
    mock_pipeline_ctx = AsyncMock()
    mock_pipeline_ctx.__aenter__.return_value = mock_pipe
    mock_pipeline_ctx.__aexit__.return_value = None
    mock_redis.pipeline.return_value = mock_pipeline_ctx

    with patch("app.services.embedding_service.get_redis_client", return_value=mock_redis):
        # 1. First call -> Cache Miss -> Calls API -> Writes to Redis pipeline
        res1 = await service.generate_embeddings(["Hello world"])
        assert res1 == [[0.1, 0.2, 0.3]]
        assert service.client.aio.models.embed_content.call_count == 1
        assert mock_pipe.setex.call_count == 1

        # 2. Second call -> Simulate Cache Hit
        mock_redis.mget.return_value = [b"[0.1, 0.2, 0.3]"]
        res2 = await service.generate_embeddings(["Hello world"])
        assert res2 == [[0.1, 0.2, 0.3]]
        # API count remains 1 because Redis hit!
        assert service.client.aio.models.embed_content.call_count == 1


@pytest.mark.asyncio
async def test_generate_embeddings_fail_open_on_redis_error():
    service = EmbeddingService()
    
    mock_emb_1 = MagicMock()
    mock_emb_1.values = [0.4, 0.5, 0.6]
    mock_response = MagicMock()
    mock_response.embeddings = [mock_emb_1]
    
    service.client = MagicMock()
    service.client.aio.models.embed_content = AsyncMock(return_value=mock_response)

    # Redis throws connection error
    mock_redis = AsyncMock()
    mock_redis.mget.side_effect = RuntimeError("Redis connection error")

    with patch("app.services.embedding_service.get_redis_client", return_value=mock_redis):
        res = await service.generate_embeddings(["Test fail open"])
        # Should gracefully fall back to Gemini API without raising exception
        assert res == [[0.4, 0.5, 0.6]]
        assert service.client.aio.models.embed_content.call_count == 1
