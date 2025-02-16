from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

def test_gmail_access():
    load_dotenv()
    
    # Using just the tokens from OAuth Playground
    creds = Credentials(
        token=os.getenv('GMAIL_ACCESS_TOKEN'),
        refresh_token=os.getenv('GMAIL_REFRESH_TOKEN'),
        token_uri='https://oauth2.googleapis.com/token',
        # Using OAuth Playground's default client credentials
        client_id='407408718192.apps.googleusercontent.com',
        client_secret='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',
        scopes=['https://www.googleapis.com/auth/gmail.readonly']
    )
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"Connected to Gmail: {profile['emailAddress']}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_gmail_access()