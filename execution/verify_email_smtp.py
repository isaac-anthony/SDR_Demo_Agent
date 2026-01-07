import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

def verify_smtp_config():
    """ 
    Sends a test email to the configured sender (self-test) 
    to verify SMTP connectivity.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    
    if not smtp_user or not smtp_pass:
        print("❌ SMTP Config Missing (SMTP_USER/SMTP_PASS)")
        return False
        
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        
        # Send a quick test email to self
        msg = f"Subject: Brine-Engine SMTP Test\n\nSMTP Connectivity Verified."
        server.sendmail(smtp_user, smtp_user, msg)
        server.quit()
        print("✅ SMTP Health: Connected & Test Email Sent")
        return True
    except Exception as e:
        print(f"❌ SMTP Health Failed: {e}")
        return False

# For standalone execution
if __name__ == "__main__":
    verify_smtp_config()
