import hashlib
import json

from google import genai

from app.core.config import settings
from app.core.logging import logger
from app.core.redis import get_redis_client


class EmbeddingService:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def _generate_cache_key(self, text: str) -> str:
        """
        Generates a deterministic SHA-256 key for a text string and model identifier.
        """
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"embedding:v1:{settings.gemini_embedding_model}:{text_hash}"

    async def _get_cached_embeddings(
        self,
        texts: list[str],
    ) -> tuple[dict[int, list[float]], list[int]]:
        """
        Fetches cached embeddings for a list of texts using Redis mget.
        Returns:
            - cached_map: dict mapping text index -> list[float]
            - missing_indices: list of text indices that missed cache
        """
        if not settings.embedding_cache_enabled:
            return {}, list(range(len(texts)))

        redis = get_redis_client()
        if redis is None:
            return {}, list(range(len(texts)))

        cached_map = {}
        missing_indices = []
        keys = [self._generate_cache_key(t) for t in texts]

        try:
            raw_results = await redis.mget(keys)
            for idx, raw_val in enumerate(raw_results):
                if raw_val is not None:
                    try:
                        embedding = json.loads(raw_val.decode("utf-8"))
                        cached_map[idx] = embedding
                    except Exception:
                        missing_indices.append(idx)
                else:
                    missing_indices.append(idx)
        except Exception as exc:
            logger.warning("Redis mget error, falling back to API | error=%s", exc)
            return {}, list(range(len(texts)))

        return cached_map, missing_indices

    async def _set_cached_embeddings(
        self,
        texts: list[str],
        generated_map: dict[int, list[float]],
        missing_indices: list[int],
    ) -> None:
        """
        Stores newly generated embeddings into Redis with configured TTL.
        Uses a Redis pipeline for zero extra network roundtrips.
        """
        if not settings.embedding_cache_enabled or not missing_indices:
            return

        redis = get_redis_client()
        if redis is None:
            return

        try:
            async with redis.pipeline(transaction=False) as pipe:
                for idx in missing_indices:
                    key = self._generate_cache_key(texts[idx])
                    val = json.dumps(generated_map[idx]).encode("utf-8")
                    pipe.setex(key, settings.embedding_cache_ttl, val)
                await pipe.execute()
        except Exception as exc:
            logger.warning("Redis pipeline write error | error=%s", exc)

    async def generate_embedding(
        self,
        text: str,
    ) -> list[float]:

        embeddings = await self.generate_embeddings(
            [text]
        )

        return embeddings[0]

    async def generate_embeddings(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        # 1. Check Redis cache first
        cached_map, missing_indices = await self._get_cached_embeddings(texts)

        if len(cached_map) == len(texts):
            logger.info("Embedding cache HIT (100%%) | count=%d", len(texts))
            return [cached_map[i] for i in range(len(texts))]

        # 2. Extract texts that missed cache
        uncached_texts = [texts[i] for i in missing_indices]
        newly_generated: list[list[float]] = []

        # 3. Call Gemini API in batches for uncached texts
        for start in range(
            0,
            len(uncached_texts),
            settings.embedding_batch_size,
        ):
            batch = uncached_texts[
                start:start + settings.embedding_batch_size
            ]

            response = (
                await self.client.aio.models.embed_content(
                    model=settings.gemini_embedding_model,
                    contents=batch,
                )
            )

            batch_embeddings = [
                embedding.values
                for embedding in response.embeddings
            ]

            if len(batch_embeddings) != len(batch):
                raise ValueError(
                    "Embedding response count does not match "
                    "the request batch size."
                )

            newly_generated.extend(batch_embeddings)

        # 4. Map newly generated embeddings back to original indices
        generated_map = {}
        for missing_idx, emb in zip(missing_indices, newly_generated):
            generated_map[missing_idx] = emb

        # 5. Save newly generated embeddings to Redis cache asynchronously
        await self._set_cached_embeddings(texts, generated_map, missing_indices)

        # 6. Reassemble final result array maintaining original order
        final_embeddings = []
        for i in range(len(texts)):
            if i in cached_map:
                final_embeddings.append(cached_map[i])
            else:
                final_embeddings.append(generated_map[i])

        hit_rate = (len(cached_map) / len(texts)) * 100
        logger.info(
            "Embedding generation completed | total=%d | cache_hits=%d | api_calls=%d | hit_rate=%.1f%%",
            len(texts),
            len(cached_map),
            len(uncached_texts),
            hit_rate,
        )

        return final_embeddings

