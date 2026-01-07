import argparse
import asyncio
import os
import smtplib
import random
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from execution.state_manager import StateManager, LeadStatus
from dotenv import load_dotenv

load_dotenv()

# Configuration
SENDER_NAME = "Isaac Gutierrez"
SENDER_EMAIL = os.getenv("SMTP_USER")
# We assume SMTP_PASS is also in env
CALENDLY_LINK = "https://calendly.com/brineaiconsulting/30min"

# Templates Strategy (A/B Testing)
TEMPLATES = [
    {
        "name": "Deal-First (100 Leads)",
        "subject": "100 custom leads for {business_name} next week?",
        "body": """Hi {lead_name},

{personalized_hook}

At Brine.ai, we’ve built an AI 'SDR Agent' that handles your prospecting and initial outreach on autopilot.

Our Guarantee: I will generate 100 personalized, high-intent leads for you in the next 7 days. If we don't hit that number, you don't pay a cent.

We handle the heavy lifting (finding the leads and sending the custom intros) so your office staff can focus entirely on closing deals and being on-site.

Do you have 10 minutes soon to see the initial batch of leads we’ve already identified for {business_name}?

Best,
Isaac Gutierrez | Founder and Architect @ Brine.AI
"""
    },
    {
        "name": "AI Employee (Operational)",
        "subject": "Implementing your new AI Employee at {business_name}",
        "body": """Hi {lead_name},

{personalized_hook}

We specialize in building Agentic Sales Engines that act as your 24/7 digital office assistant. Our agents find the leads, send the first touch, and even answer basic FAQs before they ever hit your desk.

The Brine.ai Beta Offer: We’ll put 100 custom leads in your inbox this week. If they aren't the highest quality leads you've seen this year, the service is free.

Would you be open to a 10-minute kickoff call soon to see how we can take 'prospecting' off your plate entirely?

Best,
Isaac Gutierrez | Founder and Architect @ Brine.AI
Book Your Call Here: {booking_link}
"""
    },
    {
        "name": "Niche Growth",
        "subject": "Scaling {business_name}’s {niche} pipeline",
        "body": """Hi {lead_name},

{personalized_hook}

I saw {business_name} is highly rated in {city}, but in this market, even a 5-minute delay in replying to a lead can mean a lost job.

We specialize in building Agentic Sales Engines that act as your 24/7 digital office assistant.

The Brine.ai Beta Offer: We’ll put 100 custom leads in your inbox this week. If they aren't the highest quality leads you've seen this year, the service is free.

Would you be open to a 10-minute kickoff call soon to see how we can take 'prospecting' off your plate entirely?

Best,
Isaac Gutierrez | Founder and Architect @ Brine.AI
Book Your Call Here: {booking_link}
"""
    }
]

import base64
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        try:
            with open('token.json', 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"❌ Failed to load token pickle: {e}")
            return None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("❌ OAuth Token invalid or missing scopes. Run sync_to_sheet.py first to auth.")
            return None
    return build('gmail', 'v1', credentials=creds)

def send_email(to_email, subject, body):
    try:
        service = get_gmail_service()
        if not service:
            return False
            
        message = MIMEMultipart()
        message['to'] = to_email
        message['from'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        message['subject'] = subject
        msg = MIMEText(body)
        message.attach(msg)
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        body = {'raw': raw_message}
        
        message = service.users().messages().send(userId="me", body=body).execute()
        print(f"    ✅ Email sent via Gmail API (ID: {message['id']})")
        return True
    except Exception as e:
        print(f"❌ Failed to send to {to_email} via API: {e}")
        return False

async def run_outreach_campaign(state_manager, limit=5, dry_run=False, override_email=None):
    """
    Sends 'Drip' emails to Synced leads. 
    If override_email is set, sends ALL emails to that address (for testing).
    """
    print(f"📧 Starting Outreach Campaign (Limit: {limit})...")
    
    # Get leads that are 'Synced' (meaning they are qualified and verified) or 'Failed' (retry)
    candidates = state_manager.get_leads_by_status(LeadStatus.SYNCED) + state_manager.get_leads_by_status(LeadStatus.FAILED)
    
    # Filter for leads with emails
    valid_candidates = [l for l in candidates if l.get("email") and "@" in l.get("email")]
    
    print(f"  Found {len(valid_candidates)} candidates ready for outreach.")
    
    sent_count = 0
    
    for lead in valid_candidates:
        if sent_count >= limit:
            break
            
        # Determine Recipient
        original_email = lead.get("email")
        start_email = override_email if override_email else original_email
        
        email = start_email
        name = lead.get("title")
        niche = lead.get("niche", "Business")
        city = lead.get("city", "your area")
        hook = lead.get("personalized_hook", "I noticed your impressive work online.")
        
        # Prepare content (A/B Test)
        template = random.choice(TEMPLATES)
        subject = template["subject"].format(business_name=name, niche=niche, city=city)
        body = template["body"].format(
            lead_name="Team", 
            personalized_hook=hook,
            business_name=name,
            niche=niche,
            city=city,
            sender_name=SENDER_NAME,
            booking_link=CALENDLY_LINK
        )
        
        print(f"  Sending to {name} ({email}) using '{template['name']}'...")
        
        if not dry_run:
            success = send_email(email, subject, body)
            if success:
                state_manager.update_lead_data(lead, {"last_contacted": str(datetime.now())}, LeadStatus.SENT)
                print("    ✅ Sent.")
                sent_count += 1
                
                # DRIP DELAY (Random 8-12 minutes to average 10m)
                delay = random.randint(500, 700) 
                print(f"    💤 Sleeping {delay}s (~10m) for safety...")
                await asyncio.sleep(delay)
            else:
                state_manager.update_lead_data(lead, {}, LeadStatus.FAILED)
        else:
            print(f"    [DRY RUN] Simulating email to {email} (Override: {override_email})")
            print(f"    Subject: {subject}")
            print("    --- BODY START ---")
            print(body)
            print("    --- BODY END ---")
            sent_count += 1
            await asyncio.sleep(1)

    print(f"Outreach Batch Complete. Sent {sent_count} emails.")

if __name__ == "__main__":
    from datetime import datetime # Need this import for the module run
    sm = StateManager()
    # Usage: python3 execution/outreach_campaign.py --start
    asyncio.run(run_outreach_campaign(sm, limit=2, dry_run=True))
