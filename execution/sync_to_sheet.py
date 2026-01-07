import os.path
import pickle
import json
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import gspread
from dotenv import load_dotenv
from execution.state_manager import LeadStatus

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_creds():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except:
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)
            with open('token.json', 'wb') as token:
                pickle.dump(creds, token)
    return creds

def sync_leads(state_manager, leads):
    print(f"🔄 Starting Sync for {len(leads)} leads...")
    
    creds = get_creds()
    gc = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not sheet_id:
        print("Error: GOOGLE_SHEETS_ID not found.")
        return

    sh = gc.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)
    
    # Headers
    headers = [
        "Date Added", "Status", "Years in Business", "Business Name", 
        "Lead Score", "Description", "Email", "Phone", "Rating", "Review Count", 
        "Personalized Hook", "Website"
    ]
    
    current_headers = worksheet.row_values(1)
    if not current_headers:
        worksheet.append_row(headers)
    
    # Read existing data for Upsert
    existing_records = worksheet.get_all_records()
    # Map website -> row index (approx, strictly we should use cell address but this works for upsert)
    # We use 2-based index because row 1 is headers
    website_map = {str(r.get("Website", "")).lower().rstrip('/'): i+2 for i, r in enumerate(existing_records)}
    
    rows_to_append = []
    
    for lead in leads:
        url = lead.get("website", "")
        clean_url = str(url).lower().rstrip('/')
        
        row_data = [
            datetime.now().strftime("%Y-%m-%d"),
            lead.get("status", "Discovered"), # Use current state status later?
            lead.get("years_in_business", ""),
            lead.get("title", ""),
            lead.get("lead_score", ""),
            lead.get("company_description", ""),
            lead.get("email", ""),
            lead.get("phone", ""), # Maps might scrape phone, need to ensure we capture it
            lead.get("rating", ""),
            lead.get("reviewsCount", ""),
            lead.get("personalized_hook", ""),
            url
        ]
        
        if clean_url in website_map:
            # Update
            row_idx = website_map[clean_url]
            try:
                # Update specific range
                range_name = f"A{row_idx}:L{row_idx}" 
                worksheet.update(values=[row_data], range_name=range_name)
                # print(f"  Updated row {row_idx} for {url}")
            except Exception as e:
                print(f"  Error updating {url}: {e}")
        else:
            # Insert
            rows_to_append.append(row_data)
            
        # Update State to SYNCED
        state_manager.update_lead_data(lead, {}, LeadStatus.SYNCED)

    if rows_to_append:
        worksheet.append_rows(rows_to_append)
        print(f"  Added {len(rows_to_append)} new rows.")
    
    print("✅ Sync Complete.")

if __name__ == "__main__":
    from execution.state_manager import StateManager
    sm = StateManager()
    leads = sm.get_all_leads()
    sync_leads(sm, leads)
