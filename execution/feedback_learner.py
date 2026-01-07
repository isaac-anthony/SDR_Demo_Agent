import json
import os
from execution.state_manager import StateManager, LeadStatus

STRATEGY_FILE = "directives/hook_strategy.json"

def analyze_performance():
    print("📈 Analyzing Performance & Learning...")
    sm = StateManager()
    all_leads = sm.get_all_leads()
    
    # Calculate stats
    sent = len([l for l in all_leads if l.get("status") == LeadStatus.SENT.value])
    replied = len([l for l in all_leads if l.get("status") == LeadStatus.REPLIED.value])
    
    reply_rate = (replied / sent * 100) if sent > 0 else 0
    
    print(f"  Sent: {sent} | Replies: {replied} | Rate: {reply_rate:.1f}%")
    
    # Simple Heuristic: If Rate < 2% after 20 sends, flag strategy
    current_strategy = {
        "avoid_hooks": [],
        "focus_hooks": []
    }
    
    if os.path.exists(STRATEGY_FILE):
        with open(STRATEGY_FILE, "r") as f:
            current_strategy = json.load(f)
            
    # In a real system, we'd have tagged each lead with "HookType: YearsInBusiness"
    # For now, we simulate the logic:
    if sent > 20 and reply_rate < 2.0:
        print("  ⚠️ Low performance detected. Updating strategy.")
        if "years_in_business" not in current_strategy["avoid_hooks"]:
            current_strategy["avoid_hooks"].append("years_in_business")
            current_strategy["focus_hooks"].append("high_review_volume")
            
            with open(STRATEGY_FILE, "w") as f:
                json.dump(current_strategy, f, indent=2)
            print("  ✅ Updated directives/hook_strategy.json: Avoiding 'Years in Business'.")
    else:
        print("  ✅ Strategy is stable.")

if __name__ == "__main__":
    analyze_performance()
