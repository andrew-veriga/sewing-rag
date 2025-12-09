"""API client wrapper for PDF2AlloyDB API."""
import requests
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class PDF2AlloyDBClient:
    """Client for interacting with PDF2AlloyDB API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def process_document(
        self,
        file_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF document from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            filename: Filename to process (if file_id not provided)
            
        Returns:
            Document response dictionary
        """
        url = f"{self.base_url}/api/documents/process"
        payload = {}
        if file_id:
            payload['file_id'] = file_id
        elif filename:
            payload['filename'] = filename
        else:
            raise ValueError("Either file_id or filename must be provided")
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def batch_process_documents(
        self,
        file_ids: Optional[List[str]] = None,
        filenames: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple PDF documents.
        
        Args:
            file_ids: List of Google Drive file IDs
            filenames: List of filenames to process
            
        Returns:
            Batch processing result
        """
        url = f"{self.base_url}/api/documents/batch-process"
        payload = {}
        if file_ids:
            payload['file_ids'] = file_ids
        elif filenames:
            payload['filenames'] = filenames
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_documents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all processed documents.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of document dictionaries
        """
        url = f"{self.base_url}/api/documents"
        params = {'limit': limit, 'offset': offset}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_document(self, doc_id: UUID) -> Dict[str, Any]:
        """
        Get a document with all its instructions.
        
        Args:
            doc_id: Document UUID
            
        Returns:
            Document with instructions dictionary
        """
        url = f"{self.base_url}/api/documents/{doc_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def search_documents(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "documents"
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            search_type: Type of search ('documents' or 'instructions')
            
        Returns:
            List of search results
        """
        url = f"{self.base_url}/api/documents/search"
        payload = {
            'query': query,
            'limit': limit,
            'search_type': search_type
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_drive_files(self) -> Dict[str, Any]:
        """
        List all PDF files available in Google Drive folder.
        
        Returns:
            Dictionary with files list and count
        """
        url = f"{self.base_url}/api/drive/files"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def delete_document(self, doc_id: UUID) -> None:
        """
        Delete a document and all its instructions.
        
        Args:
            doc_id: Document UUID
        """
        url = f"{self.base_url}/api/documents/{doc_id}"
        response = self.session.delete(url)
        response.raise_for_status()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status.
        
        Returns:
            Health status dictionary
        """
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def reconnect_database(self) -> Dict[str, Any]:
        """
        Manually reconnect to the database.
        
        Returns:
            Reconnection status dictionary
        """
        url = f"{self.base_url}/admin/reconnect-db"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()

