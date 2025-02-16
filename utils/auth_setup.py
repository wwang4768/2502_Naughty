from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
import json
from pathlib import Path

def setup_gmail_credentials():
    """
    Interactive setup for Gmail OAuth2 credentials
    """
    # Define the scopes you need
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    
    creds = None
    creds_path = Path('config/credentials/token.json')
    client_secrets_path = Path('config/credentials/client_secrets.json')

    # Check if we have valid credentials
    if creds_path.exists():
        creds = Credentials.from_authorized_user_file(str(creds_path), SCOPES)

    # If credentials don't exist or are invalid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secrets_path.exists():
                raise FileNotFoundError(
                    "Please download client_secrets.json from Google Cloud Console "
                    "and place it in config/credentials/ directory"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials
        creds_path.parent.mkdir(parents=True, exist_ok=True)
        with open(creds_path, 'w') as token:
            token.write(creds.to_json())
            
    return creds

if __name__ == "__main__":
    setup_gmail_credentials()