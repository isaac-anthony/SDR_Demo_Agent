import json
import os
from enum import Enum
from datetime import datetime

class LeadStatus(Enum):
    DISCOVERED = "Discovered"
    ENRICHED = "Enriched"
    SYNCED = "Synced"
    FAILED = "Failed"
    SENT = "Sent"
    REPLIED = "Replied"
    UNINTERESTED = "Uninterested"

class StateManager:
    def __init__(self, filepath=".tmp/progress.json"):
        self.filepath = filepath
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading state: {e}. Starting fresh.")
                return {"leads": {}}
        return {"leads": {}}

    def _save_state(self):
        # Create dir if not exists
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(self.state, f, indent=2)

    def add_lead(self, lead):
        """Adds a discovered lead to the state if it doesn't exist."""
        # Use website (normalized) as key, fallback to Title if no website
        key = self._get_key(lead)
        if not key:
            return # Skip invalid leads

        if key not in self.state["leads"]:
            self.state["leads"][key] = {
                "data": lead,
                "status": LeadStatus.DISCOVERED.value,
                "history": [f"{datetime.now().isoformat()}: Discovered"]
            }
            self._save_state()
            return True # New lead added
        return False # Duplicate

    def update_lead_data(self, lead, additional_data, new_status=None):
        """Updates lead data and optionally status."""
        key = self._get_key(lead)
        if key and key in self.state["leads"]:
            self.state["leads"][key]["data"].update(additional_data)
            if new_status:
                self.state["leads"][key]["status"] = new_status.value
                self.state["leads"][key]["history"].append(f"{datetime.now().isoformat()}: {new_status.value}")
            self._save_state()

    def get_leads_by_status(self, status):
        """Returns a list of leads with a specific status."""
        return [
            item["data"] 
            for item in self.state["leads"].values() 
            if item["status"] == status.value
        ]
    
    def get_all_leads(self):
        return [item["data"] for item in self.state["leads"].values()]

    def _get_key(self, lead):
        """Generates a unique key for the lead."""
        website = lead.get("website")
        if website:
            return website.lower().rstrip('/').replace('www.', '')
        return lead.get("title") # Fallback, though less reliable

# Usage Example:
# sm = StateManager()
# sm.add_lead({"title": "Test Corp", "website": "test.com"})
