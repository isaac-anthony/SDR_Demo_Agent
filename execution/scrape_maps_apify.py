import os
import json
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

def main():
    print("Executing scrape_maps_apify.py...")
    
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise ValueError("APIFY_TOKEN not found in .env")

    client = ApifyClient(token)

    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Google Maps for leads.")
    parser.add_argument("--industry", type=str, default="HVAC", help="Target industry (e.g. 'Plumbers', 'CPA')")
    parser.add_argument("--location", type=str, default="Miami, FL", help="Target location")
    args = parser.parse_args()

    search_query = f"{args.industry} in {args.location}"
    print(f"Searching for: {search_query}")

    # Actor ID for Google Maps Scraper
    ACTOR_ID = "compass/crawler-google-places"
    
    # Example input - this should eventually come from arguments or config
    run_input = {
        "searchStringsArray": [search_query],
        "maxCrawledPlacesPerSearch": 10,
        "language": "en",
    }

    print(f"Starting actor {ACTOR_ID} run...")
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    
    print(f"Actor run finished. Dataset ID: {run['defaultDatasetId']}")
    
    # Fetch results
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
    
    # Save to .tmp
    os.makedirs(".tmp", exist_ok=True)
    output_path = ".tmp/raw_maps_leads.json"
    with open(output_path, "w") as f:
        json.dump(dataset_items, f, indent=2)
    
    print(f"Saved {len(dataset_items)} items to {output_path}")

if __name__ == "__main__":
    main()
