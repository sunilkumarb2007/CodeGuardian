import sys
sys.path.append('D:\\CodeGuardian\\backend')
import asyncio
from app.services.inspection_service import RepositoryInspectionService

def run():
    svc = RepositoryInspectionService()
    res = svc.inspect_repository("https://github.com/sunilkumarb2007/JavaAPICheck")
    print("Static Passed:", res.static_analysis_passed)
    print("Build Passed:", res.build_passed)
    print("Test Passed:", res.test_passed)
    if hasattr(res, 'static_analysis_details') and res.static_analysis_details:
        print("Exit Code:", res.static_analysis_details.get("exit_code"))
        print("Command:", res.static_analysis_details.get("command"))
        print("Duration:", res.static_analysis_details.get("duration"))
        print("STDOUT LEN:", len(res.static_analysis_details.get("stdout", "")))
        print("STDERR LEN:", len(res.static_analysis_details.get("stderr", "")))
        print("STDERR:", res.static_analysis_details.get("stderr", "")[:500])
        print("STDOUT:", res.static_analysis_details.get("stdout", "")[:500])
        if res.static_analysis_details.get("exit_code") != 0:
            print("STDOUT END:", res.static_analysis_details.get("stdout", "")[-500:])

if __name__ == "__main__":
    run()
