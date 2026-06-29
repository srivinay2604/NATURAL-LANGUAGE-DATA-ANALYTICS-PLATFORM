import os
import json
import logging
import hashlib
import redis
import numpy as np
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Constants
CACHE_PREFIX = "nl_cache:"
_redis_client = None
_redis_failed = False

def get_redis_client():
    """
    Retrieves or initializes the Redis client instance.
    Returns None if Redis is unavailable.
    """
    global _redis_client, _redis_failed
    if _redis_failed:
        return None
    if _redis_client is None:
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        password = os.getenv("REDIS_PASSWORD", None)
        if not password or password.strip() == "":
            password = None
            
        try:
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                socket_timeout=2.0,
                socket_connect_timeout=2.0
            )
            # Ping to verify connection
            client.ping()
            _redis_client = client
            logger.info("Connected to Redis semantic cache successfully.")
        except Exception as e:
            _redis_failed = True
            logger.warning(f"Redis connection failed: {e}. Semantic caching will be disabled.")
            _redis_client = None
    return _redis_client


def is_available() -> bool:
    return get_redis_client() is not None


def cosine_similarity(v1, v2) -> float:
    """Computes cosine similarity between two vectors."""
    arr1 = np.array(v1, dtype=np.float32)
    arr2 = np.array(v2, dtype=np.float32)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return float(np.dot(arr1, arr2) / (norm1 * norm2))


def semantic_search(question_vector: list) -> dict | None:
    """
    Searches Redis for a semantically similar question based on vector similarity.
    Returns the cached result payload or None.
    """
    client = get_redis_client()
    if not client:
        return None

    try:
        similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.90"))
        keys = client.keys(f"{CACHE_PREFIX}*")
        
        best_similarity = -1.0
        best_payload = None
        
        for key in keys:
            data_bytes = client.get(key)
            if not data_bytes:
                continue
            try:
                data = json.loads(data_bytes.decode('utf-8'))
                cached_vector = data.get("vector")
                if not cached_vector:
                    continue
                
                sim = cosine_similarity(question_vector, cached_vector)
                if sim >= similarity_threshold and sim > best_similarity:
                    best_similarity = sim
                    best_payload = data.get("result_json")
            except Exception as parse_err:
                logger.warning(f"Failed to parse cache key {key}: {parse_err}")
                continue
                
        if best_payload:
            logger.info(f"Semantic cache hit with similarity {best_similarity:.4f}")
            return best_payload
            
        return None
    except Exception as e:
        logger.warning(f"Redis semantic search error: {e}")
        return None


def save(question: str, question_vector: list, result_json: dict):
    """
    Saves the question, vector, and result payload to Redis.
    """
    client = get_redis_client()
    if not client:
        return

    try:
        ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        q_hash = hashlib.md5(question.strip().lower().encode('utf-8')).hexdigest()
        key = f"{CACHE_PREFIX}{q_hash}"
        
        payload = {
            "question": question,
            "vector": question_vector,
            "result_json": result_json
        }
        
        client.setex(key, ttl, json.dumps(payload))
        logger.info(f"Saved query to Redis cache (key: {key}, TTL: {ttl}s).")
    except Exception as e:
        logger.warning(f"Failed to save to Redis cache: {e}")


def clear_all():
    """
    Clears all cache entries from Redis.
    """
    client = get_redis_client()
    if not client:
        return

    try:
        keys = client.keys(f"{CACHE_PREFIX}*")
        if keys:
            client.delete(*keys)
            logger.info(f"Cleared {len(keys)} entries from Redis cache.")
        else:
            logger.info("Redis cache is already empty.")
    except Exception as e:
        logger.warning(f"Failed to clear Redis cache: {e}")
