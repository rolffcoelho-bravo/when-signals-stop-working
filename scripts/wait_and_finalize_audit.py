import time
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "outputs/v3/development_execution_results"

def main():
    print("Starting audit finalization daemon...")
    while True:
        csv_files = list(RESULTS_DIR.glob("*.csv"))
        count = len(csv_files)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Progress: {count}/918 batches completed.")
        
        if count >= 918:
            print("All 918 batches completed! Finalizing audit...")
            try:
                subprocess.run([sys.executable, str(ROOT / "scripts/finalize_v3_final_release_audit.py")], check=True, cwd=str(ROOT))
                print("Successfully generated V3_FINAL_RELEASE_AUDIT.json!")
            except subprocess.CalledProcessError as e:
                print(f"Failed to generate audit: {e}")
            break
            
        # Wait 10 minutes before checking again
        time.sleep(600)

if __name__ == "__main__":
    main()
