import asyncio
import os
import random
import json
from openai import OpenAI
from dotenv import load_dotenv
from execution.state_manager import StateManager, LeadStatus
from execution.sync_to_sheet import get_creds
import gspread

load_dotenv()

QUALITY_PROMPT = """
You are a Quality Assurance Auditor for a Lead Gen Agency.
Your Task: Grade the following "Personalized Hook" for a prospective client.

The Hook must:
1. Sound professional but conversational (iPhone style).
2. Specifically mention a human achievement (years in business, reviews).
3. Connect that achievement to "automating their process".
4. NOT sound generic or robotic.

Input:
Company: {company}
Hook: "{hook}"

Output JSON:
{{
  "grade": "PASS" or "FAIL",
  "reason": "Short explanation",
  "robotic_score": int (0-10, where 10 is very robotic)
}}
"""

async def audit_hooks(leads):
    print(f"🧐 Auditing Quality of {len(leads)} leads...")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    issues = 0
    
    for lead in leads:
        hook = lead.get("personalized_hook")
        name = lead.get("title")
        if not hook:
            continue
            
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": QUALITY_PROMPT.format(company=name, hook=hook)}
                ],
                response_format={ "type": "json_object" }
            )
            data = json.loads(response.choices[0].message.content)
            
            if data["grade"] == "FAIL" or data["robotic_score"] > 6:
                print(f"  ❌ Quality Alert for '{name}': {data['reason']} (Robotic: {data['robotic_score']})")
                issues += 1
            else:
                print(f"  ✅ Quality Pass: {name}")
                
        except Exception as e:
            print(f"  Error auditing lead: {e}")

    if issues > 0:
        print(f"⚠️ Warning: {issues}/{len(leads)} hooks failed quality checks. Check your prompt.")
    else:
        print("✅ Hook Quality looks good.")

def check_sheet_duplicates(local_leads):
    print("📋 Checking for Duplicate Data in Sheet...")
    try:
        creds = get_creds()
        gc = gspread.authorize(creds)
        sheet_id = os.getenv("GOOGLE_SHEETS_ID")
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)
        
        sheet_data = worksheet.get_all_records()
        sheet_urls = {str(r.get("Website", "")).lower().rstrip('/') for r in sheet_data}
        
        duplicates = 0
        for lead in local_leads:
            url = str(lead.get("website", "")).lower().rstrip('/')
            if url in sheet_urls:
                duplicates += 1
                
        print(f"ℹ️ {duplicates} leads in local state already exist in the Sheet.")
        return duplicates
    except Exception as e:
        print(f"❌ Failed to check sheet duplicates: {e}")
        return -1

async def main():
    sm = StateManager()
    all_leads = sm.get_all_leads()
    enriched_leads = [l for l in all_leads if l.get("personalized_hook")]
    
    # 1. Sample Audit (Random 3)
    if enriched_leads:
        sample = random.sample(enriched_leads, min(3, len(enriched_leads)))
        await audit_hooks(sample)
    else:
        print("No enriched leads to audit.")

    # 2. Dedup Check
    check_sheet_duplicates(all_leads)

if __name__ == "__main__":
    asyncio.run(main())
