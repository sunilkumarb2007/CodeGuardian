import time
from app.demo.demo_runner import DemoRunner

def test_demo_runner():
    runner = DemoRunner()
    run_id = "test-run-id-123"
    
    print("Initializing...")
    runner.initialize_run(run_id)
    print(runner.get_run(run_id))
    
    print("\nExecuting asynchronously...")
    # Run synchronously for test
    runner.execute_async(run_id)
    
    print("\nState after hitting approval:")
    print(runner.get_run(run_id)["current_stage"], runner.get_run(run_id)["status"])
    
    print("\nApproving...")
    runner.approve_and_continue(run_id)
    
    print("\nFinal State:")
    print(runner.get_run(run_id)["current_stage"], runner.get_run(run_id)["status"])

if __name__ == "__main__":
    test_demo_runner()
