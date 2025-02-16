from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
import json
from .settings import GMAIL_SETTINGS, CREDENTIALS_DIR

class CredentialManager:
    def __init__(self):
        self.credentials_dir = CREDENTIALS_DIR
        self.credentials_dir.mkdir(exist_ok=True)
        
    def get_gmail_credentials(self):
        """Get or refresh Gmail API credentials"""
        creds_path = self.credentials_dir / "gmail_token.json"
        
        creds = None
        if creds_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(creds_path), GMAIL_SETTINGS["scopes"]
            )
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": GMAIL_SETTINGS["client_id"],
                            "client_secret": GMAIL_SETTINGS["client_secret"],
                            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token"
                        }
                    },
                    GMAIL_SETTINGS["scopes"]
                )
                creds = flow.run_local_server(port=0)
                
            # Save credentials
            with open(creds_path, "w") as token:
                token.write(creds.to_json())
                
        return creds
    
    def get_gemini_credentials(self):
        """Get Gemini API credentials"""
        return {"api_key": GEMINI_SETTINGS["api_key"]}