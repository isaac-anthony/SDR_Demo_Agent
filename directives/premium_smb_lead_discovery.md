# Directive: Premium SMB/SME Lead Discovery & Personalization (V2 - Hybrid Standard)

## Goal
Identify and qualify high-intent service-based businesses with "Automation Potential." Extract deep contact data (Email + Socials) using a hybrid cloud/local approach and generate hyper-personalized outreach hooks.

## Inputs (Standard Configuration)
- **Target Industries:** High-frequency service (e.g., `["HVAC", "Real Estate Agents", "Law Firms", "Medical Clinics", "Roofing"]`).
- **Target Locations:** Specific City/County, State.
- **Max Leads per Run:** 10-50 (Configurable).

## Qualification Criteria (The "Qualified Lead" Standard)
*Filters applied via `execution/filter_leads.py` then `execution/scrape_website_context.py`.*
1.  **Review Count:** **10 to 2,000+**. (Ensures they are an active, growing business).
2.  **Contact Depth:** MUST have at least ONE valid outreach path:
    - Primary: **Validated Email**.
    - Secondary: **LinkedIn, Facebook, or Instagram**.
    - Backup: **Verified Business Phone**.
3.  **Lead Scoring (1-10 Scale):**
    - **Score 9-10 (Elite):** 100+ reviews, professional website, high-value niche (Law/HVAC), clearly busy office.
    - **Score 7-8 (Strong):** 50-100 reviews, active website, solid reputation.
    - **Score 5-6 (Average):** 10-50 reviews, functional website.
    - **Score 1-4 (Low):** Under 10 reviews (Too new), No website (Too low-tech), or 1,000+ reviews (Likely enterprise-level/rigid IT).
4.  **Automation Readiness:** 
    - **Active Website:** MANDATORY.
    - **Legacy/Simple Sites:** HIGH PRIORITY for modernization.

## Workflow (3-Layer Universal Hybrid Approach)

### Phase 1: High-Volume Discovery (Google Maps Visual Agent)
1.  **Action:** Call `execution/scrape_directory_local.py`.
2.  **Logic:** Visual Playwright scrape of Google Maps. Searches for `target_niche` across `target_cities`.
3.  **Data Capture:** Extracts Business Name, Website, and "Years in Business" (if available).
4.  **Output:** `.tmp/leads_to_enrich.json`.

### Phase 2: Hybrid Enrichment (The "Unblockable" Standard)
*Executed via `execution/scrape_website_context.py`.*

1.  **Layer 1: Cloud Enrichment (Apify)**
    - Run Actor `vdrmota/contact-info-scraper`.
    - Purpose: Efficiently pull emails and social links from bulk lists.
    - Settings: Max Depth 2, Max Pages 20.
2.  **Layer 2: Local Playwright Fallback (Stealth Mode)**
    - If Layer 1 fails to find an email/socials:
    - Action: Launch local Playwright with `playwright-stealth`.
    - Deep Logic: 
        - **Slow Scroll:** Scroll to the bottom of the page to reveal hidden/lazy-loaded footers.
        - **Multi-Page:** Visit home + "Contact", "About", or "Team" pages.
        - **Source Scan:** Scan both text content and HTML source (for `mailto:` links).
3.  **Layer 3: AI Personalization (The "Solution Architect" Standard)**
    - Generate a **Company Description** (1 concise sentence).
    - Generate a **Personalized Hook** (2-sentence intro using the Brine AI Framework):
        - **Lead with Human Achievement**: Reference years in business, awards, or specific milestones.
        - **Position as Solution Architect**: Define Brine AI as building customized agentic workflows, not just "using AI."
        - **Bridge the "Lead Leak"**: Focus on capturing every inquiry instantly so high-value leads are never missed.
        - **The "Digital Extension"**: Frame automation as a 24/7 specialist or a "digital version of your best team member."

### Phase 3: Smart Sync (Update-on-Match)
1.  **Action:** Call `execution/sync_to_sheet.py`.
2.  **Logic:** 
    - Match leads based on website URL (Case-insensitive).
    - **If Match Found:** Update existing row with new contact info (Email/Socials) and fresh hooks.
    - **If No Match:** Append as a new lead.
3.  **Deduplication:** Prevents duplicate rows while ensuring data is always the "latest and greatest."

## Technical Standards
- **Cloud Failover:** If Apify monthly usage is exceeded, scripts must automatically fallback to 100% local Playwright scraping.
- **Social Priority:** Always extract LinkedIn, Facebook, and Instagram to provide the Sales Agent with "Multi-Channel" outreach options.
- **Bot Detection:** Always use Residential Proxies (for Cloud) and Stealth Plugins (for Local) to mimic human behavior.

## Deliverables
- **Google Sheet Columns:** `Date Added` | `Status` | `Business Name` | `Lead Score` | `Description` | `Email` | `Phone` | `LinkedIn` | `Facebook` | `Instagram` | `Review Count` | `Personalized Hook` | `Website`.
