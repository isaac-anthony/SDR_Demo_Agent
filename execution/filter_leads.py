import json
import os

def main():
    print("Executing filter_leads.py...")
    
    input_path = ".tmp/raw_maps_leads.json"
    output_path = ".tmp/leads_to_enrich.json"
    
    if not os.path.exists(input_path):
        print(f"No input file found at {input_path}")
        return

    with open(input_path, "r") as f:
        raw_leads = json.load(f)
        
    print(f"Loaded {len(raw_leads)} raw leads.")
    
    qualified_leads = []
    
    for lead in raw_leads:
        # Extract fields (Apify structure varies, assuming standard Google Maps actor output)
        reviews = lead.get("reviewsCount", 0)
        rating = lead.get("totalScore", 0)
        website = lead.get("website")
        title = lead.get("title")
        phone = lead.get("phone")
        address = lead.get("address")
        city = lead.get("city")
        
        # 1. Decision Maker Tags Logic (Not possible from simple Maps scrape usually, 
        # but we pass robust leads to the next step which finds them)
        
        # 2. Must have Website
        if not website:
            print(f"Rejected {title}: No Website")
            continue
            
        # 3. Review Count: 10 to 2,000+
        if not (10 <= reviews <= 2000):
            print(f"Rejected {title}: Reviews ({reviews}) not in range")
            continue
            
        # 4. Star Rating: 3.5 to 5.0
        if not (3.5 <= rating <= 5.0):
            print(f"Rejected {title}: Rating ({rating}) not in range")
            continue
            
        # 5. Phone Check (Moved to Enrichment Phase)
        # We need at least Phone OR Email. Since we don't have Email yet, we pass everything 
        # that meets other criteria (reviews, rating, website) to enrichment.
        # If it has no phone, it might still have an email on the site.
            
        qualified_leads.append(lead)

    print(f"Filtering complete. {len(qualified_leads)} leads qualified out of {len(raw_leads)}.")
    
    with open(output_path, "w") as f:
        json.dump(qualified_leads, f, indent=2)

if __name__ == "__main__":
    main()
