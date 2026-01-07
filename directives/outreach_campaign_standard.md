# Directive: Brine AI Founders Outreach

## Goal
Execute hyper-personalized outreach to qualified leads using the "Hook & Kicker" framework. Convert leads into discovery calls for Brine AI Consulting.

## Outreach Framework: The "Hook & Kicker"
Every email must follow this strict anatomical structure to maintain a high conversion rate and avoid "spammy" patterns.

1.  **Subject Line**: Direct internal observation.
    - Format: `Observation regarding [Business Name] / Lead Gen`
2.  **The Hook (Line 1)**: Hyper-personalization via the "Brine AI Solution Architect" framework.
    - Source: `personalized_hook` from the lead data.
    - **Rule of One**: Must be exactly one sentence. If no specific achievement found, use fallback.
    - **Human Achievement Lead**: Always start by acknowledging a specific, non-generic achievement (years in business, award, milestone).
    - **Bridge the "Lead Leak" Gap**: Position Brine AI as the Solution Architect that builds "Agentic Workflows" to handle Q&A instantly and turn missed connections into sales.
    - **Fallback**: "I’ve been following [Business Name]’s work in the [Niche] space and was impressed by your local reputation."
3.  **The Kicker (Line 2)**: The irresistible "Anchor" offer.
    - Wording: "To show you the power of what we're building, I will get you 100 personalized, custom leads per week using our proprietary AI discovery systems."
    - Formatting: Must be in its own paragraph.
4.  **The Value Prop (Line 3)**: What we do.
    - Wording: "We specialize in building Agentic Workflows at Brine.ai that handle the manual heavy lifting of prospecting and outreach so you can focus entirely on closing deals."
5.  **The CTA (Line 4)**: Low-friction kickoff call.
    - Wording: "Are you available for a brief 10-minute kickoff call to see the initial batch of leads we found for you?"
    - Link: `Book Your Call Here: [Calendar Link]`

## Implementation Rules
- **Rule of One**: Start with personalization. No generic "Dear Business Owner".
- **The iPhone Tone**: No corporate jargon. No "delve", "leverage", "comprehensive". Write like a quick note sent between meetings.
- **Safety First**: 
    - Never send more than 20 emails per day during the demo phase.
    - Only send to leads with `status`: `Qualified` and a valid `email`.
    - Update the sheet `Status` to `Emailed` after a successful send.

## Workflow
1.  **Read Leads**: Pull leads from the Google Sheet or `.tmp/enriched_leads.json`.
2.  **Draft & Validate**: Construct the email body based on the framework.
3.  **Send**: Call `execution/send_intro_email.py`.
4.  **Track**: Mark as `Emailed` in the tracking sheet to prevent duplicate outreach.
5.  **Follow-up**: Call `execution/manage_inbox.py` periodically.
    -   **Logic:** Scan for unread replies, categorize them using the AI, and draft responses based on the `directives/knowledge_base.md`.
    -   **Goal:** Drive leads to the appointment link: https://calendly.com/brineaiconsulting/30min

## Knowledge Base Standard
All inbound and follow-up communication must be grounded in `directives/knowledge_base.md`. This file contains the "Source of Truth" for:
-   Product offerings (Agentic Workflows).
-   FAQ answers (Pricing, Lead Discovery methods).
-   Brand voice (iPhone-style, direct, no fluff).
