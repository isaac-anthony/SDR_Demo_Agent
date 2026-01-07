import os
import pickle
import json
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_creds():
    creds = None
    token_path = 'token.json'
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid or not all(scope in getattr(creds, 'scopes', []) for scope in SCOPES):
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        
        if not creds or not all(scope in getattr(creds, 'scopes', []) for scope in SCOPES):
            print("Refreshing credentials with Gmail Modify Scopes...")
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
    return creds

def get_gmail_service():
    creds = get_creds()
    return build('gmail', 'v1', credentials=creds)

def create_message(to, subject, message_text, thread_id):
    message = MIMEText(message_text)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes())
    return {'raw': raw.decode(), 'threadId': thread_id}

def classify_and_respond(sender_email, subject, body):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Load knowledge base
    kb_path = "directives/knowledge_base.md"
    kb_content = ""
    if os.path.exists(kb_path):
        with open(kb_path, "r") as f:
            kb_content = f.read()

    prompt = f"""
    You are an AI Sales Agent for Brine AI Consulting. You just received an email reply.
    
    KNOWLEDGE BASE:
    {kb_content}
    
    EMAIL FROM: {sender_email}
    SUBJECT: {subject}
    BODY:
    {body}
    
    TASK:
    1. Classify the intention: "Interested", "Question", "Not Interested", or "Spam".
    2. If "Interested" or "Question", write a short, direct reply (iPhone style: no fluff).
    3. Use the knowledge base to answer specific questions.
    4. Always include the Calendly link for a 10-minute chat: {os.getenv("CALENDAR_LINK", "https://calendly.com/brineaiconsulting/30min")}
    
    Output ONLY a JSON object with:
    "intention": "string",
    "reply_body": "string" (empty if Not Interested/Spam)
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"intention": "Error", "reply_body": ""}

def main():
    print("Executing manage_inbox.py (AI Inbox Manager)...")
    service = get_gmail_service()
    
    # Search for unread emails for brineaiconsulting@gmail.com
    results = service.users().messages().list(userId='me', q='is:unread').execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("No unread messages found.")
        return

    processed_count = 0
    for msg in messages:
        msg_id = msg['id']
        thread_id = msg['threadId']
        
        # Get full message content
        full_msg = service.users().messages().get(userId='me', id=msg_id).execute()
        headers = full_msg['payload'].get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        
        # Extract body (Simplified)
        parts = full_msg['payload'].get('parts', [])
        body = ""
        if 'body' in full_msg['payload'] and full_msg['payload']['body'].get('data'):
             body = base64.urlsafe_b64decode(full_msg['payload']['body']['data']).decode()
        elif parts:
             for part in parts:
                 if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                     body = base64.urlsafe_b64decode(part['body']['data']).decode()
                     break

        print(f"Processing email from {sender} - {subject}")
        
        analysis = classify_and_respond(sender, subject, body)
        intention = analysis.get("intention")
        reply_text = analysis.get("reply_body")
        
        print(f"  Intention: {intention}")
        
        if intention in ["Interested", "Question"] and reply_text:
            print(f"  Drafting/Sending reply to {sender}...")
            # We want to reply to the thread. The 'To' should be the original 'From'.
            # We also typically prepend "Re: " to the subject if not there.
            reply_subject = subject if subject.startswith("Re: ") else f"Re: {subject}"
            
            # Find the actual email address from 'From' field (e.g. "Name <email@site.com>")
            import re
            email_match = re.search(r'<(.+)>', sender)
            to_email = email_match.group(1) if email_match else sender

            reply_msg = create_message(to_email, reply_subject, reply_text, thread_id)
            try:
                service.users().messages().send(userId='me', body=reply_msg).execute()
                print(f"  Reply sent successfully.")
            except Exception as e:
                print(f"  Failed to send reply: {e}")
        
        # Mark as read (Remove 'UNREAD' label)
        service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
        processed_count += 1

    print(f"Inbox management complete. Processed {processed_count} emails.")

if __name__ == "__main__":
    main()
