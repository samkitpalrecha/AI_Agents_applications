import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText

class GmailClient:
    SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # For reading emails
    'https://www.googleapis.com/auth/gmail.send'      # For sending emails
    ]
    
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        Initialize the GmailClient with credentials and token files.
        Args:
            credentials_file (str): Path to the Gmail API credentials.json file.
            token_file (str): Path to the token.json file to store user's tokens.
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API and return a service instance."""
        creds = None
        # Load existing token if available
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        # If credentials are not valid or unavailable, prompt login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the new token for future use
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        return build('gmail', 'v1', credentials=creds)
    
    def fetch_latest_email(self):
        """
        Fetch the latest email from the user's Gmail inbox.
        Returns:
            dict: Contains email 'subject', 'from', and 'body'.
        """
        try:
            results = self.service.users().messages().list(userId='me', maxResults=1).execute()
            messages = results.get('messages', [])
            if not messages:
                print("No emails found.")
                return None
            
            message_id = messages[0]['id']
            message = self.service.users().messages().get(userId='me', id=message_id).execute()
            payload = message['payload']
            headers = payload.get('headers', [])
            
            email_data = {}
            for header in headers:
                if header['name'] == 'Subject':
                    email_data['subject'] = header['value']
                if header['name'] == 'From':
                    email_data['from'] = header['value']    
            
            # Decode the email body
            if 'parts' in payload:
                email_data['body'] = base64.urlsafe_b64decode(payload['parts'][0]['body']['data']).decode('utf-8')
            else:
                email_data['body'] = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            
            return email_data
        except Exception as e:
            print(f"An error occurred while fetching email: {e}")
            return None

    def send_email(self, recipient, subject, body):
        """
        Send an email using Gmail API.
        Args:
            recipient (str): Recipient's email address.
            subject (str): Subject of the email.
            body (str): Body of the email.
        """
        try:
            # Create the email
            message = MIMEText(body)
            message['to'] = recipient
            message['subject'] = subject
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the email
            message = {'raw': raw_message}
            sent_message = self.service.users().messages().send(userId='me', body=message).execute()
            print(f"Email sent successfully. Message ID: {sent_message['id']}")
        except Exception as e:
            print(f"An error occurred while sending the email: {e}")
