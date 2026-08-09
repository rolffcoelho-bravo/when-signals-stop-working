import json
import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "outputs/v3/development_execution_plan/authorization_candidate_manifest.json"
LOCK_PATH = ROOT / "V3_G5_REAL_EXECUTION_AUTHORIZATION_LOCK.json"

def run(command: list[str]) -> str:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed: {' '.join(command)}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip()

def main():
    if not CANDIDATE_PATH.exists():
        print(f"Candidate manifest not found at {CANDIDATE_PATH}")
        sys.exit(1)
        
    print("Reading authorization candidate manifest...")
    manifest = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    
    if manifest.get("status") != "AUTHORIZATION_CANDIDATE_PLAN_MATERIALIZED":
        print(f"Invalid candidate status: {manifest.get('status')}")
        sys.exit(1)

    print("Verifying Git working tree is clean...")
    run(["git", "diff", "--quiet"])
    run(["git", "diff", "--cached", "--quiet"])
    
    commit = run(["git", "rev-parse", "HEAD"])
    
    print("Promoting candidate to AUTHORIZATION_GRANTED...")
    lock = manifest.copy()
    lock["schema_version"] = "v3.g5-real-execution-authorization-lock.v2"
    lock["status"] = "AUTHORIZATION_GRANTED"
    lock["real_development_execution_authorized"] = True
    lock["real_development_model_fitting_authorized"] = True
    lock["authorization_commit"] = commit
    
    # We do NOT authorize selection or admission yet.
    lock["development_pipeline_selection_authorized"] = False
    lock["development_pipeline_admission_authorized"] = False
    lock["signal_establishment_segment_access_authorized"] = False
    lock["final_framework_reserve_access_authorized"] = False

    print(f"Writing lock to {LOCK_PATH.name}...")
    LOCK_PATH.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Authorization finalized successfully.")
    print("Real execution is now authorized. You may begin batch processing on the cluster.")

if __name__ == "__main__":
    main()
