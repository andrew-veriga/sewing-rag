"""API routes for document processing and retrieval."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import logging
import tempfile
import os
from pathlib import Path

from app.db.connection import get_db
from app.models.schemas import (
    ProcessDocumentRequest,
    DocumentResponse,
    InstructionResponse,
    SearchRequest,
    SearchResult,
    DocumentWithInstructions
)
from app.services.drive_service import drive_service
from app.services.pdf_service import pdf_service
from app.services.alloydb_service import alloydb_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/documents/process", response_model=DocumentResponse, status_code=201)
async def process_document(
    request: ProcessDocumentRequest,
    background_tasks: BackgroundTasks = None
):
    """
    Process a PDF document from Google Drive.
    
    Downloads the PDF, extracts structured data using Gemini, and stores in AlloyDB.
    """
    try:
        # Determine file to process
        if request.filename:
            # If filename is provided, check database first to avoid unnecessary Drive API calls
            existing_doc = alloydb_service.get_document_by_filename(request.filename)
            if existing_doc:
                logger.info(f"Document {request.filename} already exists, returning existing document")
                return DocumentResponse.model_validate(existing_doc)
            
            # Document doesn't exist, get file info from Drive
            file_info = drive_service.get_file_by_name(request.filename)
            if not file_info:
                raise HTTPException(status_code=404, detail=f"File '{request.filename}' not found in Google Drive")
            filename = file_info['name']
            file_id = file_info['id']
        elif request.file_id:
            # Get file info by file ID (need to call Drive API to get filename)
            try:
                file_info = drive_service.get_file_info(request.file_id)
                filename = file_info.get('name')
                file_id = request.file_id
            except Exception as e:
                logger.error(f"Error getting file info for file_id {request.file_id}: {str(e)}")
                raise HTTPException(status_code=404, detail=f"File with ID '{request.file_id}' not found in Google Drive")
            
            # Check if document already exists
            existing_doc = alloydb_service.get_document_by_filename(filename)
            if existing_doc:
                logger.info(f"Document {filename} already exists, returning existing document")
                return DocumentResponse.model_validate(existing_doc)
        else:
            raise HTTPException(status_code=400, detail="Either file_id or filename must be provided")
        
        # Download PDF from Google Drive
        logger.info(f"Downloading PDF {filename} from Google Drive")
        pdf_path = drive_service.download_file(file_id)
        
        try:
            # Upload PDF to Gemini and extract structured data
            logger.info(f"Extracting structured data from {filename}")
            images, gemini_file = pdf_service.get_tutorial_images(pdf_path)
            instructions_data = pdf_service.extract_structured_tutorial(gemini_file)
            
            # Store in AlloyDB using SQL functions
            logger.info(f"Storing {filename} in AlloyDB")
            doc_id = alloydb_service.store_document_with_instructions(
                filename=filename,
                instructions_data=instructions_data
            )
            
            # Get the stored document
            document = alloydb_service.get_document(doc_id)
            if not document:
                raise HTTPException(status_code=500, detail="Failed to retrieve stored document")
            
            return DocumentResponse.model_validate(document)
            
        finally:
            # Clean up temporary file
            try:
                pdf_file = Path(pdf_path)
                if pdf_file.exists():
                    pdf_file.unlink(missing_ok=True)
                    logger.debug(f"Cleaned up temporary file {pdf_path}")
            except OSError as e:
                # Handle OS errors (permissions, file in use, etc.)
                logger.warning(f"Could not remove temporary file {pdf_path}: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.post("/documents/batch-process", status_code=202)
async def batch_process_documents(
    file_ids: List[str] = None,
    filenames: List[str] = None
):
    """
    Process multiple PDF documents from Google Drive.
    
    Returns a list of document IDs that will be processed.
    """
    try:
        if file_ids:
            files_to_process = [
                {'id': fid, 'name': None} for fid in file_ids
            ]
        elif filenames:
            files_to_process = []
            for filename in filenames:
                file_info = drive_service.get_file_by_name(filename)
                if file_info:
                    files_to_process.append({
                        'id': file_info['id'],
                        'name': file_info['name']
                    })
        else:
            # Process all PDFs in the folder
            pdf_files = drive_service.list_pdf_files()
            files_to_process = [
                {'id': f['id'], 'name': f['name']} for f in pdf_files
            ]
        
        processed_ids = []
        errors = []
        
        for file_info in files_to_process:
            try:
                request = ProcessDocumentRequest(file_id=file_info['id'])
                result = await process_document(request, BackgroundTasks())
                processed_ids.append(str(result.id))
            except Exception as e:
                errors.append({
                    'file_id': file_info['id'],
                    'filename': file_info['name'],
                    'error': str(e)
                })
        
        return {
            'processed': len(processed_ids),
            'document_ids': processed_ids,
            'errors': errors
        }
    
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in batch processing: {str(e)}")


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all processed documents."""
    try:
        documents = alloydb_service.list_documents(limit=limit, offset=offset)
        return [DocumentResponse.model_validate(doc) for doc in documents]
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@router.get("/documents/{doc_id}", response_model=DocumentWithInstructions)
async def get_document(
    doc_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a document with all its instructions."""
    try:
        document = alloydb_service.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        instructions = alloydb_service.get_document_instructions(doc_id)
        
        return DocumentWithInstructions(
            document=DocumentResponse.model_validate(document),
            instructions=[InstructionResponse.model_validate(instr) for instr in instructions]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting document: {str(e)}")


@router.post("/documents/search", response_model=List[SearchResult])
async def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Perform vector similarity search on documents or instructions."""
    try:
        if request.search_type == "documents":
            results = alloydb_service.search_documents(
                query_text=request.query,
                limit=request.limit
            )
            return [
                SearchResult(
                    id=UUID(r['id']),
                    similarity=r['similarity'],
                    title=r['title'],
                    brief=r['brief']
                )
                for r in results
            ]
        elif request.search_type == "instructions":
            results = alloydb_service.search_instructions(
                query_text=request.query,
                limit=request.limit
            )
            return [
                SearchResult(
                    id=UUID(r['id']),
                    similarity=r['similarity'],
                    header=r['header'],
                    instruction=r['instruction'],
                    page=r['page']
                )
                for r in results
            ]
        else:
            raise HTTPException(
                status_code=400,
                detail="search_type must be 'documents' or 'instructions'"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")


@router.get("/drive/files")
async def list_drive_files():
    """List all PDF files available in Google Drive folder."""
    try:
        files = drive_service.list_pdf_files()
        return {
            'files': files,
            'count': len(files)
        }
    except Exception as e:
        logger.error(f"Error listing Drive files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing Drive files: {str(e)}")


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(
    doc_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a document and all its instructions."""
    try:
        deleted = alloydb_service.delete_document(doc_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

