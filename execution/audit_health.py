import asyncio
import os
from openai import OpenAI
from execution.state_manager import StateManager
from execution.verify_email_smtp import verify_smtp_config

async def check_connectivity():
    print("  Checking Connectivity...")
    
    # 1. OpenAI Check
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        client.models.list()
        print("  ✅ OpenAI API: Connected")
    except Exception as e:
        print(f"  ❌ OpenAI API Failed: {e}")
        return False
        
    # 2. Google Sheets API (via Sync Module Check)
    try:
        from execution.sync_to_sheet import get_creds
        creds = get_creds()
        if creds and creds.valid:
            print("  ✅ Google Sheets API: Connected")
        else:
            print("  ❌ Google Sheets API: Invalid Credentials")
            return False
    except Exception as e:
        print(f"  ❌ Google Sheets API Failed: {e}")
        return False

    return True

async def check_stealth():
    print("  Checking Stealth Layer...")
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, # Headless for check
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = await browser.new_page()
            await Stealth().apply_stealth_async(page)
            # Simple check: Does google challenge us immediately?
            # Or use a bot check site. For speed, we just ping google.
            await page.goto("https://www.google.com/search?q=test", timeout=10000)
            title = await page.title()
            if "Google" in title:
                print("  ✅ Stealth Check: Passed (Google access OK)")
            else:
                print(f"  ⚠️ Stealth Check: Suspicious Title ({title})")
                
            await browser.close()
    except Exception as e:
        print(f"  ❌ Stealth Check Failed: {e}")
        return False
    return True

async def run_audit():
    print("🏥 Starting 'Brine Audit' (System Health)...")
    
    # 1. Connectivity
    if not await check_connectivity():
        print("❌ Audit Failed: Connectivity Issues")
        return False
        
    # 2. Stealth
    if not await check_stealth():
        print("❌ Audit Failed: Stealth Issues")
        return False
        
    # 3. SMTP
    if not verify_smtp_config():
        print("⚠️ Audit Warning: SMTP Issue (Proceeding anyway)")
        
    print("✅ Pre-Flight Audit Passed. System is Healthy.\n")
    return True

if __name__ == "__main__":
    asyncio.run(run_audit())
