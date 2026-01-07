import os
import pickle
import json
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

# SCOPES for Sheets and Gmail
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_creds():
    creds = None
    # Use the same token.json as sync_to_sheet.py
    token_path = 'token.json'
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # Check if scopes match or if creds are valid
    if not creds or not creds.valid or not all(scope in creds.scopes for scope in SCOPES):
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # If refresh fails (e.g. scopes changed), re-auth
                creds = None
        
        if not creds or not all(scope in creds.scopes for scope in SCOPES):
            print("Refreshing credentials with Gmail Scopes...")
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
    return creds

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes())
    return {'raw': raw.decode()}

def send_message(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print(f'Message Id: {message["id"]} sent to {message.get("to", "recipient")}')
        return message
    except Exception as error:
        print(f'An error occurred: {error}')
        return None

def main():
    print("Starting Outreach Campaign (Brine AI)...")
    
    creds = get_creds()
    service = build('gmail', 'v1', credentials=creds)
    
    # Load enriched leads
    input_path = ".tmp/enriched_leads.json"
    if not os.path.exists(input_path):
        print("No leads found to email.")
        return

    with open(input_path, "r") as f:
        leads = json.load(f)

    sender_name = os.getenv("SENDER_NAME", "Founder")
    calendar_link = os.getenv("CALENDAR_LINK", "https://calendly.com/brineaiconsulting/30min")
    
    sent_count = 0
    for lead in leads:
        # Only send to qualified leads with an email
        if lead.get("status") != "Qualified" or not lead.get("email"):
            continue
            
        business_name = lead.get("title", "your business")
        to_email = lead.get("email")
        
        # Format Subject
        subject = f"Observation regarding {business_name} / Lead Gen"
        
        # Format Body
        hook = lead.get("personalized_hook")
        if not hook or len(hook) < 10:
            hook = f"I’ve been following {business_name}’s work in the local space and was impressed by your reputation."

        body = f"""Hi {business_name},

{hook}

To show you the power of what we're building, I will get you 100 personalized, custom leads per week using our proprietary AI discovery systems.

We specialize in building Agentic Workflows at Brine.ai that handle the manual heavy lifting of prospecting and outreach so you can focus entirely on closing deals.

Are you available for a brief 10-minute kickoff call to see the initial batch of leads we found for you?

Book Your Call Here: {calendar_link}

Best regards,

{sender_name}
Founder, Brine.ai"""

        print(f"Sending email to {business_name} ({to_email})...")
        msg = create_message('me', to_email, subject, body)
        result = send_message(service, 'me', msg)
        
        if result:
            sent_count += 1
            # Mark as emailed
            lead["status"] = "Emailed"

    # Save updated status
    with open(input_path, "w") as f:
        json.dump(leads, f, indent=2)
        
    print(f"Outreach complete. Total emails sent: {sent_count}")

if __name__ == "__main__":
    main()
