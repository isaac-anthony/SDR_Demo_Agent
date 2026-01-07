import argparse
import asyncio
import sys
from execution.state_manager import StateManager, LeadStatus
from execution.scrape_directory_local import discover_leads
from execution.scrape_website_context import enrich_leads
from execution.sync_to_sheet import sync_leads
from execution.audit_health import run_audit

# WATCHDOG CONFIG
MAX_FAILURES_PER_LEAD = 3

def parse_args():
    parser = argparse.ArgumentParser(description="Brine-Engine-V2: Autonomous Lead Gen")
    parser.add_argument("--limit", type=int, default=30, help="Target number of NEW leads")
    parser.add_argument("--batch-size", type=int, default=10, help="Leads per browser batch")
    parser.add_argument("--city", type=str, default="Miami, FL", help="Target City")
    parser.add_argument("--niche", type=str, default="Personal Injury Lawyer", help="Target Niche")
    parser.add_argument("--debug", action="store_true", help="Run with headful browser")
    parser.add_argument("--audit", action="store_true", help="Run Pre-Flight Health Check & Single Lead Test")
    parser.add_argument("--test-email", type=str, help="Send test emails to this address (Live Test)")
    return parser.parse_args()

async def main():
    args = parse_args()

    # --- AUDIT MODE ---
    if args.audit:
        print("🔍 RUNNING IN AUDIT/DIAGNOSTIC MODE")
        healthy = await run_audit()
        if not healthy:
            print("🛑 System Unhealthy. Aborting.")
            return
        
        # Test Run: 1 Lead
        print("🧪 Running Test Lead through Pipeline...")
        args.limit = 1
        args.batch_size = 1
        # Continue to execution logic below...

    print(f"🚀 Starting Brine-Engine-V2 | Target: {args.limit} Leads in {args.city}")
    sm = StateManager()

    # ... (phases 1, 2, 3) ...
    # Skip showing them for brevity in replacement, focusing on PHASE 4 block logic

    # --- PHASE 1: DISCOVERY ---
    try:
        await discover_leads(state_manager=sm, niche=args.niche, city=args.city, limit=args.limit, batch_size=args.batch_size, debug=args.debug)
    except Exception as e:
        print(f"❌ Critical Discovery Failure: {e}")
        return

    # --- PHASE 2: ENRICHMENT ---
    leads_to_enrich = sm.get_leads_by_status(LeadStatus.DISCOVERED)
    print(f"\n--- PHASE 2: ENRICHMENT ({len(leads_to_enrich)} leads) ---")
    if leads_to_enrich:
        try:
            await enrich_leads(state_manager=sm, leads=leads_to_enrich, batch_size=args.batch_size, debug=args.debug)
        except Exception as e:
             print(f"❌ Enrichment Batch Failed: {e}")
    else:
        print("No new leads to enrich.")

    # --- PHASE 3: SYNC ---
    print("\n--- PHASE 3: DELIVERY ---")
    leads_to_sync = sm.get_all_leads() 
    if leads_to_sync:
        try:
            sync_leads(state_manager=sm, leads=leads_to_sync)
        except Exception as e:
            print(f"❌ Sync Failed: {e}")
    else:
        print("Nothing to sync.")

    # --- PHASE 4: OUTREACH (Drip) ---
    if args.limit > 0 and not args.audit:
        print("\n--- PHASE 4: OUTREACH (Drip) ---")
        from execution.outreach_campaign import run_outreach_campaign
        
        # Determine mode
        is_dry_run = True
        override = None
        
        if args.test_email:
            print(f"  🧪 TEST MODE: Sending LIVE emails to {args.test_email}")
            is_dry_run = False
            override = args.test_email
            
        try:
            await run_outreach_campaign(state_manager=sm, limit=5, dry_run=is_dry_run, override_email=override)
        except Exception as e:
             print(f"❌ Outreach Failed: {e}")
        
    print("\n✅ Brine-Engine-V2 Run Complete.")
    print(f"Final Count: {len(sm.get_all_leads())} leads tracked.")

if __name__ == "__main__":
    asyncio.run(main())
