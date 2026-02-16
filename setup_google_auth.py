"""Setup script for Google Docs OAuth authentication.

Run this script locally to authenticate with Google and generate
the token file needed for server-side Google Docs export.
"""
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes needed for Google Docs and Drive
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive'
]

CREDENTIALS_PATH = '/data/.openclaw/workspace/google-drive-credentials.json'
TOKEN_PATH = '/data/.openclaw/workspace/.google-token.json'


def setup_google_auth():
    """Run OAuth flow to get and save credentials."""
    creds = None
    
    # Load credentials file
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ Credentials file not found: {CREDENTIALS_PATH}")
        return
    
    with open(CREDENTIALS_PATH, 'r') as f:
        creds_data = json.load(f)
    
    print("🌐 Starting Google OAuth flow...")
    print("   A browser window will open for you to authorize the app.")
    print("   Please sign in with the Google account that owns the docs.")
    print()
    
    # Create flow
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_PATH,
        SCOPES
    )
    
    # Run local server for OAuth
    creds = flow.run_local_server(port=0)
    
    # Save the token
    with open(TOKEN_PATH, 'w') as token:
        token.write(creds.to_json())
    
    print()
    print("✅ Token saved successfully!")
    print(f"   Location: {TOKEN_PATH}")
    print()
    print("You can now use Google Docs export in CoverageIQ.")
    print("Copy this token file to your server if needed.")


if __name__ == "__main__":
    setup_google_auth()
