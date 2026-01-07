import subprocess
import time
import sys
import argparse
from execution.state_manager import StateManager, LeadStatus

def run_process(cmd):
    """Runs the main engine process and returns the exit code."""
    print(f"🐕 GuardDog: Starting process -> {' '.join(cmd)}")
    try:
        # We use Popen to stream output to console in real-time
        process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
        process.wait()
        return process.returncode
    except Exception as e:
        print(f"🐕 GuardDog: Process launch failed: {e}")
        return -1

def main():
    parser = argparse.ArgumentParser(description="Brine-Engine GuardDog: Self-Healing Watchdog")
    parser.add_argument("--limit", type=str, default="30")
    parser.add_argument("--city", type=str, default="Miami, FL")
    parser.add_argument("--niche", type=str, default="Personal Injury Lawyer")
    args = parser.parse_args()

    MAX_RETRIES = 3
    retries = 0
    
    cmd = [
        "python3", "main.py",
        "--limit", args.limit,
        "--city", args.city,
        "--niche", args.niche
    ]
    
    while retries < MAX_RETRIES:
        exit_code = run_process(cmd)
        
        if exit_code == 0:
            print("🐕 GuardDog: Engine finished successfully. Good boy.")
            break
        else:
            retries += 1
            print(f"🐕 GuardDog: Engine crashed (Exit Code: {exit_code}). Retry {retries}/{MAX_RETRIES} in 5 seconds...")
            
            # Diagnostic: Read state to see progress
            try:
                sm = StateManager()
                processed = len(sm.get_all_leads())
                print(f"   (Current Progress: {processed} total leads tracked)")
            except:
                pass
                
            time.sleep(5)
            
    if retries >= MAX_RETRIES:
        print("🐕 GuardDog: Max retries reached. Engine is dead. Alerting human.")
        # In real life: send_slack_alert()

if __name__ == "__main__":
    main()
