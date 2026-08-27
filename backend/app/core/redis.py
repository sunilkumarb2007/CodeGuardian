import logging
import redis
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
            cls._instance._init_redis()
        return cls._instance

    def _init_redis(self):
        self.client: Optional[redis.Redis] = None
        if settings.redis_url:
            try:
                self.client = redis.from_url(settings.redis_url, decode_responses=True)
                # Quick health check
                self.client.ping()
                logger.info("Successfully connected to Redis.")
            except Exception as e:
                logger.error(f"Failed to connect to Redis at {settings.redis_url}: {e}")
                self.client = None
        else:
            logger.info("REDIS_URL not configured. Redis features will be degraded.")

    def get_client(self) -> Optional[redis.Redis]:
        return self.client

    def is_healthy(self) -> bool:
        if not self.client:
            return False
        try:
            return self.client.ping()
        except Exception:
            return False

redis_manager = RedisManager()
