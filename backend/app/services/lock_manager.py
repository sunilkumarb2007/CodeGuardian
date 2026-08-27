import logging
import threading
from typing import Dict
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)

# Fallback thread lock if redis is not configured
_local_locks: Dict[str, threading.Lock] = {}
_global_lock = threading.Lock()

from typing import Callable, Optional

class RunLock:
    """
    Optional Redis-backed lock manager for concurrency coordination.
    Uses threading.Lock as fallback if REDIS_URL is not provided.
    Ensures absolute isolation for simultaneous runs.

    Lock loss (Redis outage or expiry) is handled cooperatively:
      - heartbeat sets self._cancelled
      - calls on_loss() so orchestrator can persist failure state
      - orchestrator polls lock.cancelled in its loop and stops via normal flow
      - _thread.interrupt_main() is NOT used; it destabilises the server
    """
    def __init__(self, run_id: str, on_loss: Optional[Callable] = None):
        self.run_id = run_id
        self.on_loss = on_loss
        self.redis_client = redis_manager.get_client()
        self._local_lock = None
        self._redis_lock = None
        self._heartbeat_thread = None
        self._stop_event = threading.Event()   # set to request heartbeat stop
        self._cancelled = threading.Event()    # set when lock is lost involuntarily

        if not self.redis_client:
            with _global_lock:
                if run_id not in _local_locks:
                    _local_locks[run_id] = threading.Lock()
                self._local_lock = _local_locks[run_id]
        else:
            # 60s TTL with 20s heartbeat gives ~40s safety margin
            self._redis_lock = self.redis_client.lock(
                f"codeguardian:run:{run_id}:lock",
                timeout=60,
                thread_local=False
            )

    @property
    def cancelled(self) -> bool:
        """True if the lock was lost involuntarily (Redis outage / lease expired)."""
        return self._cancelled.is_set()

    def _heartbeat(self):
        """Renew the Redis lock every 20 seconds until stopped."""
        while not self._stop_event.wait(20.0):
            try:
                if self._redis_lock and self._redis_lock.owned():
                    self._redis_lock.reacquire()
                    logger.debug(f"Heartbeat: lock renewed for run {self.run_id}")
                else:
                    logger.error(
                        f"LOCK_LOST: Redis lock not owned for run {self.run_id}. "
                        "Signalling cooperative cancellation."
                    )
                    self._cancelled.set()
                    if self.on_loss:
                        try:
                            self.on_loss()
                        except Exception as ex:
                            logger.error(f"on_loss callback raised: {ex}")
                    break
            except Exception as e:
                logger.error(
                    f"LOCK_LOST: Failed to renew heartbeat for run {self.run_id}: {e}. "
                    "Signalling cooperative cancellation."
                )
                self._cancelled.set()
                if self.on_loss:
                    try:
                        self.on_loss()
                    except Exception as ex:
                        logger.error(f"on_loss callback raised: {ex}")
                break

    def acquire(self, blocking: bool = True, timeout: int = 30) -> bool:
        if self.redis_client:
            acquired = self._redis_lock.acquire(blocking=blocking, blocking_timeout=timeout)
            if acquired:
                self._stop_event.clear()
                self._cancelled.clear()
                self._heartbeat_thread = threading.Thread(
                    target=self._heartbeat, daemon=True, name=f"hb-{self.run_id}"
                )
                self._heartbeat_thread.start()
            return acquired
        else:
            return self._local_lock.acquire(blocking=blocking, timeout=timeout)

    def release(self):
        if self.redis_client:
            self._stop_event.set()   # signal heartbeat to stop
            if self._heartbeat_thread and self._heartbeat_thread.is_alive():
                self._heartbeat_thread.join(timeout=5.0)
            try:
                self._redis_lock.release()
            except Exception as e:
                logger.error(f"Failed to release redis lock for run {self.run_id}: {e}")
        else:
            try:
                self._local_lock.release()
            except Exception as e:
                logger.error(f"Failed to release local lock for run {self.run_id}: {e}")

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock for run {self.run_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()