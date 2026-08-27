import pytest
import time
from unittest.mock import MagicMock, patch
from app.services.lock_manager import RunLock

def test_redis_lock_same_run():
    # Acquire lock for run A
    lock_a1 = RunLock("test-run-123")
    assert lock_a1.acquire(blocking=False) == True, "Should acquire lock successfully"
    
    # Try to acquire another lock for run A
    lock_a2 = RunLock("test-run-123")
    assert lock_a2.acquire(blocking=False) == False, "Should fail to acquire lock for same run"
    
    # Release first lock
    lock_a1.release()
    
    # Should now be able to acquire
    assert lock_a2.acquire(blocking=False) == True, "Should acquire lock successfully after release"
    lock_a2.release()

def test_redis_lock_different_runs():
    # Acquire lock for run A
    lock_a = RunLock("test-run-A")
    assert lock_a.acquire(blocking=False) == True, "Should acquire lock successfully"
    
    # Acquire lock for run B
    lock_b = RunLock("test-run-B")
    assert lock_b.acquire(blocking=False) == True, "Should acquire lock successfully for different run"
    
    # Release both
    lock_a.release()
    lock_b.release()

@patch("app.services.lock_manager.redis_manager.get_client")
def test_redis_lock_heartbeat(mock_get_client):
    mock_redis = MagicMock()
    mock_get_client.return_value = mock_redis
    
    mock_lock_obj = MagicMock()
    mock_lock_obj.acquire.return_value = True
    mock_lock_obj.owned.return_value = True
    mock_redis.lock.return_value = mock_lock_obj
    
    # Acquire lock
    lock = RunLock("test-heartbeat")
    
    # Override wait time for test to just 0.1s instead of 20s
    original_wait = lock._stop_event.wait
    def fast_wait(timeout):
        return original_wait(0.1)
    lock._stop_event.wait = fast_wait
    
    assert lock.acquire(blocking=False) == True
    
    # Wait for a couple of heartbeats
    time.sleep(0.3)
    
    lock.release()
    
    # Ensure reacquire was called at least once
    assert mock_lock_obj.reacquire.call_count > 0, "Heartbeat should have reacquired the lock"
