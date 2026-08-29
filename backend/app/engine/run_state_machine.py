import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class RunState(str, Enum):
    CREATED = "CREATED"
    REPOSITORY_LOADING = "REPOSITORY_LOADING"
    INSPECTING = "INSPECTING"
    ARCHITECTURE_DETECTED = "ARCHITECTURE_DETECTED"
    FAILURE_DETECTED = "FAILURE_DETECTED"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    GHOSTTRACE_COMPLETE = "GHOSTTRACE_COMPLETE"
    MEMORY_MATCH_FOUND = "MEMORY_MATCH_FOUND"
    INVESTIGATION_RUNNING = "INVESTIGATION_RUNNING"
    PATCH_GENERATED = "PATCH_GENERATED"
    PATCH_COMPATIBLE = "PATCH_COMPATIBLE"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    PATCH_APPROVED = "PATCH_APPROVED"
    REPLAY_RUNNING = "REPLAY_RUNNING"
    BUILD_RUNNING = "BUILD_RUNNING"
    TESTS_RUNNING = "TESTS_RUNNING"
    VALIDATION_RUNNING = "VALIDATION_RUNNING"
    VALIDATED = "VALIDATED"
    DELIVERY_RUNNING = "DELIVERY_RUNNING"
    DELIVERY_PREPARING = "DELIVERY_PREPARING"
    BRANCH_CREATED = "BRANCH_CREATED"
    COMMIT_CREATED = "COMMIT_CREATED"
    PUSHED = "PUSHED"
    PULL_REQUEST_CREATED = "PULL_REQUEST_CREATED"
    DELIVERED = "DELIVERED"
    POST_MERGE_REPLAY_RUNNING = "POST_MERGE_REPLAY_RUNNING"
    POST_MERGE_VERIFIED = "POST_MERGE_VERIFIED"
    MEMORY_UPDATED = "MEMORY_UPDATED"
    COMPLETED = "COMPLETED"

    # Explicit terminal failures
    REPOSITORY_NOT_FOUND = "REPOSITORY_NOT_FOUND"
    NO_FAILURE_EVIDENCE = "NO_FAILURE_EVIDENCE"
    INVESTIGATION_FAILED = "INVESTIGATION_FAILED"
    INVESTIGATION_TIMEOUT = "INVESTIGATION_TIMEOUT"
    INVESTIGATION_SCHEMA_ERROR = "INVESTIGATION_SCHEMA_ERROR"
    PATCH_GENERATION_FAILED = "PATCH_GENERATION_FAILED"
    PATCH_CONTEXT_INVALID = "PATCH_CONTEXT_INVALID"
    PATCH_PATH_UNSAFE = "PATCH_PATH_UNSAFE"
    PATCH_LANGUAGE_MISMATCH = "PATCH_LANGUAGE_MISMATCH"
    PATCH_APPLY_FAILED = "PATCH_APPLY_FAILED"
    BASELINE_FAILURE_NOT_REPRODUCED = "BASELINE_FAILURE_NOT_REPRODUCED"
    BUILD_FAILED = "BUILD_FAILED"
    TESTS_FAILED = "TESTS_FAILED"
    REPLAY_FAILED = "REPLAY_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    REPAIR_EXHAUSTED = "REPAIR_EXHAUSTED"
    DELIVERY_AUTH_REQUIRED = "DELIVERY_AUTH_REQUIRED"
    DELIVERY_FAILED = "DELIVERY_FAILED"
    REJECTED = "REJECTED"
    LOCK_LOST = "LOCK_LOST"


# Define valid transitions
VALID_TRANSITIONS = {
    RunState.CREATED: [RunState.REPOSITORY_LOADING, RunState.REPOSITORY_NOT_FOUND],
    RunState.REPOSITORY_LOADING: [RunState.INSPECTING, RunState.REPOSITORY_NOT_FOUND],
    RunState.INSPECTING: [RunState.ARCHITECTURE_DETECTED],
    RunState.ARCHITECTURE_DETECTED: [RunState.FAILURE_DETECTED, RunState.NO_FAILURE_EVIDENCE],
    RunState.FAILURE_DETECTED: [RunState.EVIDENCE_COLLECTED],
    RunState.EVIDENCE_COLLECTED: [RunState.GHOSTTRACE_COMPLETE],
    RunState.GHOSTTRACE_COMPLETE: [RunState.MEMORY_MATCH_FOUND],
    RunState.MEMORY_MATCH_FOUND: [RunState.INVESTIGATION_RUNNING],
    RunState.INVESTIGATION_RUNNING: [
        RunState.PATCH_GENERATED, 
        RunState.INVESTIGATION_FAILED, 
        RunState.INVESTIGATION_TIMEOUT, 
        RunState.INVESTIGATION_SCHEMA_ERROR,
        RunState.PATCH_GENERATION_FAILED
    ],
    RunState.PATCH_GENERATED: [
        RunState.PATCH_COMPATIBLE,
        RunState.PATCH_CONTEXT_INVALID,
        RunState.PATCH_PATH_UNSAFE,
        RunState.PATCH_LANGUAGE_MISMATCH
    ],
    RunState.PATCH_COMPATIBLE: [RunState.REPLAY_RUNNING],
    RunState.REPLAY_RUNNING: [
        RunState.BUILD_RUNNING, 
        RunState.REPLAY_FAILED, 
        RunState.BASELINE_FAILURE_NOT_REPRODUCED,
        RunState.PATCH_APPLY_FAILED
    ],
    RunState.BUILD_RUNNING: [RunState.TESTS_RUNNING, RunState.BUILD_FAILED],
    RunState.TESTS_RUNNING: [RunState.VALIDATION_RUNNING, RunState.TESTS_FAILED],
    RunState.VALIDATION_RUNNING: [RunState.VALIDATED, RunState.VALIDATION_FAILED],
    
    # Repair loop transitions from failures back to investigation
    RunState.BUILD_FAILED: [RunState.INVESTIGATION_RUNNING, RunState.REPAIR_EXHAUSTED],
    RunState.TESTS_FAILED: [RunState.INVESTIGATION_RUNNING, RunState.REPAIR_EXHAUSTED],
    RunState.VALIDATION_FAILED: [RunState.INVESTIGATION_RUNNING, RunState.REPAIR_EXHAUSTED],
    RunState.REPLAY_FAILED: [RunState.INVESTIGATION_RUNNING, RunState.REPAIR_EXHAUSTED],
    RunState.PATCH_APPLY_FAILED: [RunState.INVESTIGATION_RUNNING, RunState.REPAIR_EXHAUSTED],
    RunState.PATCH_CONTEXT_INVALID: [RunState.INVESTIGATION_RUNNING, RunState.REPAIR_EXHAUSTED],
    RunState.PATCH_PATH_UNSAFE: [RunState.INVESTIGATION_RUNNING, RunState.REPAIR_EXHAUSTED],

    RunState.VALIDATED: [RunState.WAITING_FOR_APPROVAL],
    RunState.WAITING_FOR_APPROVAL: [RunState.PATCH_APPROVED, RunState.REJECTED],
    RunState.PATCH_APPROVED: [RunState.DELIVERY_PREPARING],
    RunState.DELIVERY_PREPARING: [RunState.DELIVERED, RunState.DELIVERY_FAILED, RunState.DELIVERY_AUTH_REQUIRED],
    RunState.DELIVERED: [RunState.POST_MERGE_REPLAY_RUNNING, RunState.MEMORY_UPDATED],
    RunState.POST_MERGE_REPLAY_RUNNING: [RunState.POST_MERGE_VERIFIED, RunState.REPLAY_FAILED],
    RunState.POST_MERGE_VERIFIED: [RunState.MEMORY_UPDATED],
    RunState.BRANCH_CREATED: [RunState.COMMIT_CREATED, RunState.DELIVERY_FAILED],
    RunState.COMMIT_CREATED: [RunState.PUSHED, RunState.DELIVERY_FAILED],
    RunState.PUSHED: [RunState.PULL_REQUEST_CREATED, RunState.DELIVERY_FAILED],
    RunState.PULL_REQUEST_CREATED: [RunState.MEMORY_UPDATED],
    RunState.MEMORY_UPDATED: [RunState.COMPLETED]
}

TERMINAL_STATES = {
    RunState.COMPLETED,
    RunState.REPOSITORY_NOT_FOUND,
    RunState.NO_FAILURE_EVIDENCE,
    RunState.INVESTIGATION_FAILED,
    RunState.INVESTIGATION_TIMEOUT,
    RunState.INVESTIGATION_SCHEMA_ERROR,
    RunState.PATCH_GENERATION_FAILED,
    RunState.PATCH_LANGUAGE_MISMATCH,
    RunState.BASELINE_FAILURE_NOT_REPRODUCED,
    RunState.REPAIR_EXHAUSTED,
    RunState.DELIVERY_AUTH_REQUIRED,
    RunState.DELIVERY_FAILED,
    RunState.REJECTED,
    RunState.LOCK_LOST
}


class InvalidStateTransitionError(Exception):
    pass


class RunStateMachine:
    def __init__(self, initial_state: RunState = RunState.CREATED):
        self.current_state = initial_state
        self.state_data: Dict[str, Any] = {}
        self.history: List[RunState] = [initial_state]

    def transition_to(self, new_state: RunState, data: Dict[str, Any] = None):
        if self.current_state in TERMINAL_STATES:
            raise InvalidStateTransitionError(f"Cannot transition from terminal state {self.current_state}")
            
        allowed_next = VALID_TRANSITIONS.get(self.current_state, [])
        if new_state not in allowed_next:
            raise InvalidStateTransitionError(f"Invalid transition from {self.current_state} to {new_state}")
            
        logger.info(f"Transitioning from {self.current_state} to {new_state}")
        self.current_state = new_state
        self.history.append(new_state)
        if data:
            self.state_data[new_state.value] = data

    def is_terminal(self) -> bool:
        return self.current_state in TERMINAL_STATES

    def get_state(self) -> RunState:
        return self.current_state
        
    def get_data(self) -> Dict[str, Any]:
        return self.state_data

    def force_fail(self, terminal_state: RunState, reason: str):
        if terminal_state not in TERMINAL_STATES:
            raise ValueError(f"{terminal_state} is not a valid terminal state")
        logger.error(f"Run failed in state {self.current_state} -> {terminal_state}: {reason}")
        
        self.current_state = terminal_state
        self.history.append(terminal_state)
        self.state_data[terminal_state.value] = {"error": reason}

