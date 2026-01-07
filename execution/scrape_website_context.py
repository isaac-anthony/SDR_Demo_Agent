import asyncio
import os
import re
import json
import dns.resolver
from openai import OpenAI
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from markdownify import markdownify as md
from execution.state_manager import LeadStatus

# Load Environment
from dotenv import load_dotenv
load_dotenv()

SYSTEM_PROMPT = """
You are a Lead Scoring & Solution Architect AI.
Tier 1 Task: Score the lead (1-10) based on:
- 15-50 Reviews (Sweet spot for growth)
- Years in Business > 5 (Established)
- No modern booking widget (Operational inefficiency)

Tier 2 Task: Master Directive - Personalization Agent (Hook Engine).
1. Objective: Generate a ONE-SENTENCE personalized opening hook.
2. Input: Business Name, Website Content.
3. Rules:
    - Length: Exactly ONE sentence.
    - Tone: Observational, professional, and congratulatory.
    - Zero "AI-isms": NEVER use "I hope this email finds you well," "I was intrigued by," or "In the ever-evolving landscape."
    - The "Human" Test: Sounds like a founder visiting the site.
4. Priority Targets:
    - Specific People (Founder/Partner names & role).
    - Awards/Recognition (Specific awards).
    - Unique Services (Niche focus).
    - Longevity/History (Years in business/community ties).
5. Examples:
    - "I was impressed to see that [Name] has been leading your litigation team in Newport Beach for over 20 years—congratulations on that longevity!"
    - "I noticed that [Business Name] was recently recognized as a Top 100 HVAC Contractor in Riverside—a well-deserved honor."
    - "I saw that you specialize in niche forensic accounting for high-net-worth individuals, which is a really unique approach to the field."
6. Fallback (Use EXACTLY if thin):
    - "I noticed [Business Name] while looking at successful businesses in the [Niche] space and was impressed by your local reputation."

Output JSON: { "score": int, "hook": string, "description": string }
"""

def check_mx_record(domain):
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except:
        return False

async def enrich_leads(state_manager, leads, batch_size=10, debug=False):
    print(f"🔬 Starting Enrichment for {len(leads)} leads...")
    
    # Load Learned Strategy
    strategy_prompt = ""
    if os.path.exists("directives/hook_strategy.json"):
        try:
            with open("directives/hook_strategy.json", "r") as f:
                strategy = json.load(f)
                avoid = ", ".join(strategy.get("avoid_hooks", []))
                focus = ", ".join(strategy.get("focus_hooks", []))
                if avoid:
                    strategy_prompt = f"\n[LEARNED CONSTRAINT]: Avoid mentioning {avoid}. Focus on {focus} instead."
                    print(f"  🧠 Applying Learned Strategy: Avoid {avoid}")
        except: pass

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Process in batches
    for i in range(0, len(leads), batch_size):
        batch = leads[i : i + batch_size]
        print(f"  Processing Batch {i//batch_size + 1} ({len(batch)} leads)...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=not debug,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            for lead in batch:
                url = lead.get("website")
                if not url:
                    state_manager.update_lead_data(lead, {}, LeadStatus.FAILED)
                    continue
                    
                print(f"    Scanning: {lead.get('title')} ({url})")
                
                try:
                    page = await context.new_page()
                    await Stealth().apply_stealth_async(page)
                    
                    try:
                        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    except:
                        # Fallback for timeouts
                        print(f"      Timeout loading {url}, skipping.")
                        await page.close()
                        state_manager.update_lead_data(lead, {}, LeadStatus.FAILED)
                        continue

                    # Extract Content (Markdown First)
                    html = await page.content()
                    markdown_text = md(html)[:8000] # Limit tokens
                    
                    # Find Emails (Regex)
                    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', markdown_text))
                    
                    # Fallback: Check Contact Page if no emails found
                    if not emails:
                        try:
                            # Look for common contact link text
                            contact_link = await page.query_selector('a[href*="contact"], a:has-text("Contact"), a:has-text("Get in Touch")')
                            if contact_link:
                                print("      No emails on home, checking Contact page...")
                                await contact_link.click(timeout=5000)
                                await page.wait_for_load_state("domcontentloaded", timeout=10000)
                                
                                # Re-scrape
                                contact_html = await page.content()
                                contact_text = md(contact_html)[:8000]
                                emails.update(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', contact_text))
                                # Append text for AI context
                                markdown_text += "\n\n--- Contact Page ---\n" + contact_text
                        except Exception as e:
                            # print(f"      Contact fallback failed: {e}")
                            pass
                    # Filter junk
                    valid_emails = [e for e in emails if not any(x in e.lower() for x in ['.png', '.jpg', '.webp', 'sentry', 'wix'])]
                    
                    # Tier 3: Validation (MX Check on first email found)
                    primary_email = valid_emails[0] if valid_emails else None
                    if primary_email:
                        domain = primary_email.split('@')[-1]
                        if not check_mx_record(domain):
                            print(f"      Invalid MX for {domain}, discarding email.")
                            primary_email = None

                    # Tier 1 & 2: AI Analysis
                    ai_data = {}
                    if markdown_text:
                        try:
                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": SYSTEM_PROMPT + strategy_prompt},
                                    {"role": "user", "content": f"Analyze this site content:\n{markdown_text}"}
                                ],
                                response_format={ "type": "json_object" }
                            )
                            ai_data = json.loads(response.choices[0].message.content)
                        except Exception as e:
                            print(f"      AI Error: {e}")

                    # Update State
                    enriched_data = {
                        "email": primary_email or "",
                        "lead_score": ai_data.get("score", 0),
                        "personalized_hook": ai_data.get("hook", ""),
                        "company_description": ai_data.get("description", ""),
                        "markdown_content_snippet": markdown_text[:500]
                    }
                    
                    status = LeadStatus.ENRICHED if primary_email else LeadStatus.DISCOVERED # Keep as discovered if failed to find valid email? Or mark enriched partial?
                    # Let's mark ENRICHED even if no email, so we don't loop forever.
                    state_manager.update_lead_data(lead, enriched_data, LeadStatus.ENRICHED)
                    print(f"      ✅ Enriched! Score: {enriched_data['lead_score']} | Email: {primary_email}")
                    
                    await page.close()
                    
                except Exception as e:
                    print(f"    Error processing {url}: {e}")
                    state_manager.update_lead_data(lead, {}, LeadStatus.FAILED)

            await browser.close()

if __name__ == "__main__":
    # Test block
    from execution.state_manager import StateManager
    sm = StateManager()
    # Add dummy lead if needed
    # sm.add_lead({"title": "Test", "website": "https://example.com"})
    leads = sm.get_leads_by_status(LeadStatus.DISCOVERED)
    asyncio.run(enrich_leads(sm, leads, debug=True))
