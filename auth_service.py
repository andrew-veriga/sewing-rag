import os
from google.oauth2 import service_account
from google.cloud import storage
from google import genai
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class GoogleCloudAuth:
    def __init__(self):
        self.credentials = None
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize Google Cloud credentials using service account key."""
        service_account_path = os.environ.get("GOOGLE_SERVICE_CREDENTIALS")
        
        if service_account_path and os.path.exists(service_account_path):
            # Use service account key file
            self.credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=[
                    'https://www.googleapis.com/auth/cloud-platform',
                    'https://www.googleapis.com/auth/drive.readonly'
                ]
            )
        else:
            # Fallback to application default credentials
            import google.auth
            self.credentials, _ = google.auth.default()
    
    def get_storage_client(self):
        """Get authenticated Google Cloud Storage client."""
        return storage.Client(credentials=self.credentials)
    
    def get_gemini_client(self):
        """Get authenticated Gemini client."""
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_REGION")
        
        return genai.Client(
            project=project_id,
            location=location,
            credentials=self.credentials
        )
    
    def get_drive_client(self):
        """Get authenticated Google Drive API client."""
        return build('drive', 'v3', credentials=self.credentials)
    
    def get_service_account_email(self) -> str:
        """
        Get the service account email address.
        This is needed to share Google Drive folders with the service account.
        
        Returns:
            Service account email address
        """
        if hasattr(self.credentials, 'service_account_email'):
            return self.credentials.service_account_email
        elif hasattr(self.credentials, '_service_account_email'):
            return self.credentials._service_account_email
        else:
            # Try to get from the credentials file
            import json
            service_account_path = os.environ.get("GOOGLE_SERVICE_CREDENTIALS")
            if service_account_path and os.path.exists(service_account_path):
                with open(service_account_path, 'r') as f:
                    key_data = json.load(f)
                    return key_data.get('client_email', 'Unknown')
            return 'Unknown'

# Global instance
auth_service = GoogleCloudAuth()
