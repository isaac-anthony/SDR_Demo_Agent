import asyncio
import json
import os
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Re-exporting for compatibility if needed, but mainly used by main.py
TARGET_NICHE = "Personal Injury Lawyer"
TARGET_CITIES = ["Miami, FL", "Austin, TX", "Denver, CO", "Atlanta, GA", "Phoenix, AZ"]

async def discover_leads(state_manager, niche, city, limit, batch_size, debug=False):
    print(f"🕵️ Starting Discovery for '{niche}' in '{city}' | Target: {limit} NEW leads")
    
    leads_found_this_session = 0
    total_leads_processed = 0
    
    async with async_playwright() as p:
        # Headless toggle based on debug flag or user preference
        browser = await p.chromium.launch(
            headless=not debug, 
            slow_mo=100 if debug else 50,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        search_term = f"{niche} in {city}"
        print(f"--- Navigating to Google Maps for: {search_term} ---")
        
        try:
            await page.goto("https://www.google.com/maps", timeout=60000)
            
            # Consent Handling
            try:
                consent_btn = await page.wait_for_selector('button[aria-label="Accept all"], button[aria-label="Reject all"], span:text("Reject all")', timeout=5000)
                if consent_btn: await consent_btn.click()
            except: pass

            try:
                 # Search
                await page.wait_for_selector("input#searchboxinput, input[name='q']", timeout=10000)
                await page.fill("input#searchboxinput, input[name='q']", search_term)
                await page.keyboard.press("Enter")
                await page.wait_for_selector('div[role="feed"]', timeout=30000)
            except Exception as e:
                print(f"Error initiating search: {e}")
                await browser.close()
                return

            # Infinite Scroll Loop until limit reached
            consecutive_no_leads_scrolls = 0
            
            while leads_found_this_session < limit:
                print(f"  Scrolling... (Found {leads_found_this_session}/{limit} new leads)")
                
                # Scroll
                sidebar = await page.query_selector('div[role="feed"]')
                if sidebar:
                    await page.keyboard.press("PageDown")
                    await asyncio.sleep(random.uniform(2, 4)) # Human delay
                
                listings = await page.query_selector_all('div[role="article"]')
                
                leads_before_processing = leads_found_this_session
                
                # Process visible listings
                for listing in listings:
                    try:
                        link_el = await listing.query_selector('a[href*="/maps/place/"]')
                        if not link_el: continue
                        
                        name = await link_el.get_attribute("aria-label") or await link_el.inner_text()
                        maps_link = await link_el.get_attribute("href")
                        
                        full_text = await listing.inner_text()
                        
                        # Data Extraction
                        years_in_business = ""
                        rating_score = 0.0
                        reviews_count = 0
                        website = ""
                        
                        # Parsing Text Logic
                        lines = full_text.split('\n')
                        for line in lines:
                            if "years in business" in line.lower():
                                years_in_business = line
                            if "(" in line and ")" in line and line[0].isdigit():
                                try:
                                    parts = line.split("(")
                                    rating_score = float(parts[0].strip())
                                    reviews_count = int(parts[1].split(")")[0].replace(",",""))
                                except: pass
                        
                        # Website Heuristic
                        all_links = await listing.query_selector_all("a")
                        for lk in all_links:
                            href = await lk.get_attribute("href")
                            if href and "google.com" not in href and href.startswith("http"):
                                website = href
                                break
                        
                        lead = {
                            "title": name,
                            "website": website,
                            "reviewsCount": reviews_count,
                            "rating": rating_score,
                            "years_in_business": years_in_business,
                            "maps_link": maps_link,
                            "city": city,
                            "niche": niche
                        }
                        
                        # Add to State Manager
                        added = state_manager.add_lead(lead)
                        if added:
                            leads_found_this_session += 1
                            print(f"    [+] New Lead: {name} ({years_in_business})")
                        
                        if leads_found_this_session >= limit:
                            break
                            
                    except Exception as e:
                        # print(f"    Error parsing listing: {e}") 
                        pass
                
                if leads_found_this_session == leads_before_processing:
                    consecutive_no_leads_scrolls += 1
                    print(f"    (No new leads found in this scroll. Attempt {consecutive_no_leads_scrolls}/5)")
                else:
                    consecutive_no_leads_scrolls = 0
                
                if consecutive_no_leads_scrolls >= 5:
                    print("  Stopping Discovery: No new leads found after 5 consecutive scrolls.")
                    break

                # End of list check logic could go here, but for now we rely on the limit
                if leads_found_this_session >= limit:
                    break
                    
        except Exception as e:
            print(f"Session Error: {e}")
        finally:
            await browser.close()
            print(f"Discovery Session Ended. Found {leads_found_this_session} new leads.")

if __name__ == "__main__":
    # Test block
    from execution.state_manager import StateManager
    sm = StateManager()
    asyncio.run(discover_leads(sm, "Personal Injury Lawyer", "Miami, FL", 5, 5, debug=True))
