class ExecutionPolicy:
    """
    Centralized hard execution bounds for CodeGuardian orchestration.
    """
    COMMAND_TIMEOUT_BUILD = 300
    COMMAND_TIMEOUT_TEST = 300
    COMMAND_TIMEOUT_GIT = 60
    
    # Absolute deadline for the total investigation phase across all retries
    AI_TOTAL_DEADLINE = 180
    
    # Maximum AI response timeout in seconds per attempt
    AI_REQUEST_TIMEOUT = 120
    
    # TTL for run-level mutual exclusion locks
    LOCK_TTL = 900
    
    # Max time to wait to acquire a lock
    LOCK_ACQUIRE_TIMEOUT = 30
