"""Script to search for folders in Google Drive."""
from auth_service import auth_service

# Get the Drive API client
drive = auth_service.get_drive_client()

# List all folders
results = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder'",
    fields="files(id, name)"
).execute()

folders = results.get('files', [])
print(f"Found {len(folders)} folders:\n")
for folder in folders:
    print(f"Name: {folder['name']}, ID: {folder['id']}")