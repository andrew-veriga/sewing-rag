"""Google Drive service for accessing and downloading PDF files."""
import os
import tempfile
import logging
from typing import List, Optional, Dict
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
import io
import ssl
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import sys
from pathlib import Path

# Add parent directory to path to import auth_service
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth_service import auth_service
from app.config import GOOGLE_DRIVE_FOLDER_ID

logger = logging.getLogger(__name__)


class DriveService:
    """Service for interacting with Google Drive API."""
    
    def __init__(self):
        """Initialize Drive service with authenticated client."""
        self.drive_client = auth_service.get_drive_client()
        self.folder_id = GOOGLE_DRIVE_FOLDER_ID
        
        if not self.folder_id:
            logger.warning("GOOGLE_DRIVE_FOLDER_ID not set. Drive operations may fail.")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ssl.SSLError, ConnectionError, OSError)),
        reraise=True
    )
    def get_file_info(self, file_id: str) -> Dict[str, str]:
        """
        Get file metadata by file ID with retry logic for SSL errors.
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Dictionary with file metadata
        """
        try:
            return self.drive_client.files().get(
                fileId=file_id,
                supportsAllDrives=True
            ).execute()
        except ssl.SSLError as e:
            logger.warning(f"SSL error getting file info for {file_id}, will retry: {str(e)}")
            raise
        except (ConnectionError, OSError) as e:
            logger.warning(f"Network error getting file info for {file_id}, will retry: {str(e)}")
            raise
    
    def list_pdf_files(self, folder_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all PDF files in the specified Google Drive folder.
        
        Args:
            folder_id: Google Drive folder ID. If None, uses GOOGLE_DRIVE_FOLDER_ID from config.
            
        Returns:
            List of dictionaries containing file metadata: id, name, mimeType
        """
        target_folder = folder_id or self.folder_id
        
        if not target_folder:
            raise ValueError("No folder ID provided and GOOGLE_DRIVE_FOLDER_ID not set")
        
        try:
            # First, verify we can access the folder
            try:
                folder_info = self.drive_client.files().get(
                    fileId=target_folder,
                    fields="id, name, mimeType",
                    supportsAllDrives=True  # Required for Shared Drives
                ).execute()
                logger.info(f"Accessing folder: {folder_info.get('name')} (ID: {target_folder})")
            except Exception as e:
                logger.error(f"Cannot access folder {target_folder}. Error: {str(e)}")
                logger.error("Make sure the service account has access to this folder.")
                raise
            
            # Query for PDF files in the folder
            query = f"'{target_folder}' in parents and mimeType='application/pdf' and trashed=false"
            logger.debug(f"Query: {query}")
            
            results = self.drive_client.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime)",
                orderBy="name",
                pageSize=1000,  # Increase page size
                supportsAllDrives=True,  # Required for Shared Drives
                includeItemsFromAllDrives=True  # Required for Shared Drives
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} PDF files in folder {target_folder}")
            
            # If no PDFs found, list all files to help debug
            if len(files) == 0:
                logger.warning("No PDF files found. Listing all files in folder for debugging...")
                all_files = self.list_all_files(target_folder)
                logger.info(f"Total files in folder: {len(all_files)}")
                if all_files:
                    logger.info("File types found:")
                    file_types = {}
                    for f in all_files:
                        mime = f.get('mimeType', 'unknown')
                        file_types[mime] = file_types.get(mime, 0) + 1
                    for mime, count in file_types.items():
                        logger.info(f"  {mime}: {count}")
            
            return [
                {
                    'id': file.get('id'),
                    'name': file.get('name'),
                    'mimeType': file.get('mimeType'),
                    'size': file.get('size'),
                    'modifiedTime': file.get('modifiedTime')
                }
                for file in files
            ]
        except Exception as e:
            logger.error(f"Error listing PDF files: {str(e)}")
            raise
    
    def list_all_files(self, folder_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all files (any type) in the specified Google Drive folder.
        Useful for debugging permission and access issues.
        
        Args:
            folder_id: Google Drive folder ID. If None, uses GOOGLE_DRIVE_FOLDER_ID from config.
            
        Returns:
            List of dictionaries containing file metadata
        """
        target_folder = folder_id or self.folder_id
        
        if not target_folder:
            raise ValueError("No folder ID provided and GOOGLE_DRIVE_FOLDER_ID not set")
        
        try:
            query = f"'{target_folder}' in parents and trashed=false"
            
            results = self.drive_client.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime)",
                orderBy="name",
                pageSize=1000,
                supportsAllDrives=True,  # Required for Shared Drives
                includeItemsFromAllDrives=True  # Required for Shared Drives
            ).execute()
            
            files = results.get('files', [])
            return [
                {
                    'id': file.get('id'),
                    'name': file.get('name'),
                    'mimeType': file.get('mimeType'),
                    'size': file.get('size'),
                    'modifiedTime': file.get('modifiedTime')
                }
                for file in files
            ]
        except Exception as e:
            logger.error(f"Error listing all files: {str(e)}")
            raise
    
    def download_file(self, file_id: str, output_path: Optional[str] = None) -> str:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            output_path: Optional path to save the file. If None, creates a temporary file.
            
        Returns:
            Path to the downloaded file
        """
        try:
            # Get file metadata
            file_metadata = self.drive_client.files().get(
                fileId=file_id,
                supportsAllDrives=True  # Required for Shared Drives
            ).execute()
            file_name = file_metadata.get('name', 'downloaded_file.pdf')
            
            # Determine output path
            if output_path:
                output_file = Path(output_path)
            else:
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                output_file = Path(temp_dir) / file_name
            
            # Ensure parent directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            request = self.drive_client.files().get_media(fileId=file_id)
            with open(output_file, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Download progress: {int(status.progress() * 100)}%")
            
            logger.info(f"Downloaded file {file_name} to {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            raise
    
    def get_file_by_name(self, filename: str, folder_id: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        Get a file by its name from the specified folder.
        
        Args:
            filename: Name of the file to find
            folder_id: Google Drive folder ID. If None, uses GOOGLE_DRIVE_FOLDER_ID from config.
            
        Returns:
            Dictionary with file metadata or None if not found
        """
        target_folder = folder_id or self.folder_id
        
        if not target_folder:
            raise ValueError("No folder ID provided and GOOGLE_DRIVE_FOLDER_ID not set")
        
        try:
            query = f"'{target_folder}' in parents and name='{filename}' and trashed=false"
            
            results = self.drive_client.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime)",
                supportsAllDrives=True,  # Required for Shared Drives
                includeItemsFromAllDrives=True  # Required for Shared Drives
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                file = files[0]
                return {
                    'id': file.get('id'),
                    'name': file.get('name'),
                    'mimeType': file.get('mimeType'),
                    'size': file.get('size'),
                    'modifiedTime': file.get('modifiedTime')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding file {filename}: {str(e)}")
            raise


# Global instance
drive_service = DriveService()