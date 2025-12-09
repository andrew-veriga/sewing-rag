"""AlloyDB service for database operations and AI function calls."""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.connection import get_db_context
from app.models.database import Document, Instruction
from app.models.schemas import Instructions, ImageWithText

logger = logging.getLogger(__name__)


class AlloyDBService:
    """Service for AlloyDB operations using SQL functions and ORM."""
    
    def store_document_with_instructions(
        self,
        filename: str,
        instructions_data: Instructions
    ) -> UUID:
        """
        Store a document and its instructions using AlloyDB SQL functions.
        This replaces the VectorizedTutorial function logic.
        
        Args:
            filename: Name of the PDF file
            instructions_data: Parsed Instructions object from PDF extraction
            
        Returns:
            UUID of the created document
        """
        with get_db_context() as db:
            try:
                # Call SQL function to store document with embedding
                result = db.execute(
                    text("""
                        SELECT store_document(
                            :filename, :title, :brief, :specifications,
                            :production_package, :fabric_consumption, :preprocessings
                        ) as doc_id
                    """),
                    {
                        'filename': filename,
                        'title': instructions_data.title,
                        'brief': instructions_data.brief or '',
                        'specifications': instructions_data.specifications or '',
                        'production_package': instructions_data.production_package or '',
                        'fabric_consumption': instructions_data.fabric_consumption or '',
                        'preprocessings': instructions_data.preprocessings or ''
                    }
                )
                
                doc_id = result.scalar()
                
                # Store each instruction
                for instr in instructions_data.list_instructions:
                    db.execute(
                        text("""
                            SELECT store_instruction(
                                :parent_id, :page, :header, :instruction, :box_2d
                            )
                        """),
                        {
                            'parent_id': doc_id,
                            'page': instr.page,
                            'header': instr.header,
                            'instruction': instr.instruction,
                            'box_2d': instr.box_2d
                        }
                    )
                
                db.commit()
                logger.info(f"Stored document {filename} with {len(instructions_data.list_instructions)} instructions")
                
                return doc_id
                
            except Exception as e:
                logger.error(f"Error storing document: {str(e)}")
                db.rollback()
                raise
    
    def get_document(self, doc_id: UUID) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document UUID
            
        Returns:
            Document object or None (expunged from session)
        """
        with get_db_context() as db:
            document = db.query(Document).filter(Document.id == doc_id).first()
            if document:
                # Expunge the object from the session so it can be used outside the context
                # Access all attributes first to ensure they're loaded
                _ = document.id, document.filename, document.title, document.brief
                _ = document.specifications, document.production_package
                _ = document.fabric_consumption, document.preprocessings
                _ = document.created_at, document.updated_at
                db.expunge(document)
            return document
    
    def get_document_by_filename(self, filename: str) -> Optional[Document]:
        """
        Get a document by filename.
        
        Args:
            filename: Document filename
            
        Returns:
            Document object or None (expunged from session)
        """
        with get_db_context() as db:
            document = db.query(Document).filter(Document.filename == filename).first()
            if document:
                # Expunge the object from the session so it can be used outside the context
                # Access all attributes first to ensure they're loaded
                _ = document.id, document.filename, document.title, document.brief
                _ = document.specifications, document.production_package
                _ = document.fabric_consumption, document.preprocessings
                _ = document.created_at, document.updated_at
                db.expunge(document)
            return document
    
    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """
        List all documents with pagination.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of Document objects (expunged from session)
        """
        with get_db_context() as db:
            documents = db.query(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset).all()
            # Expunge all documents from the session
            for document in documents:
                # Access all attributes first to ensure they're loaded
                _ = document.id, document.filename, document.title, document.brief
                _ = document.specifications, document.production_package
                _ = document.fabric_consumption, document.preprocessings
                _ = document.created_at, document.updated_at
                db.expunge(document)
            return documents
    
    def get_document_instructions(self, doc_id: UUID) -> List[Instruction]:
        """
        Get all instructions for a document.
        
        Args:
            doc_id: Document UUID
            
        Returns:
            List of Instruction objects (expunged from session)
        """
        with get_db_context() as db:
            instructions = db.query(Instruction).filter(Instruction.parent_id == doc_id).order_by(Instruction.page, Instruction.id).all()
            # Expunge all instructions from the session
            for instruction in instructions:
                # Access all attributes first to ensure they're loaded
                _ = instruction.id, instruction.parent_id, instruction.page
                _ = instruction.header, instruction.instruction, instruction.box_2d
                _ = instruction.created_at
                db.expunge(instruction)
            return instructions
    
    def search_documents(
        self,
        query_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search on documents.
        
        Args:
            query_text: Search query text
            limit: Maximum number of results
            
        Returns:
            List of search results with similarity scores
        """
        with get_db_context() as db:
            result = db.execute(
                text("SELECT * FROM search_documents(:query_text, :limit_count)"),
                {'query_text': query_text, 'limit_count': limit}
            )
            
            return [
                {
                    'id': row.id,
                    'filename': row.filename,
                    'title': row.title,
                    'brief': row.brief,
                    'similarity': float(row.similarity)
                }
                for row in result
            ]
    
    def search_instructions(
        self,
        query_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search on instructions.
        
        Args:
            query_text: Search query text
            limit: Maximum number of results
            
        Returns:
            List of search results with similarity scores
        """
        with get_db_context() as db:
            result = db.execute(
                text("SELECT * FROM search_instructions(:query_text, :limit_count)"),
                {'query_text': query_text, 'limit_count': limit}
            )
            
            return [
                {
                    'id': row.id,
                    'parent_id': row.parent_id,
                    'page': row.page,
                    'header': row.header,
                    'instruction': row.instruction,
                    'similarity': float(row.similarity)
                }
                for row in result
            ]
    
    def delete_document(self, doc_id: UUID) -> bool:
        """
        Delete a document and all its instructions.
        
        Args:
            doc_id: Document UUID
            
        Returns:
            True if deleted, False if not found
        """
        with get_db_context() as db:
            document = db.query(Document).filter(Document.id == doc_id).first()
            if document:
                db.delete(document)
                db.commit()
                logger.info(f"Deleted document {doc_id}")
                return True
            return False


# Global instance
alloydb_service = AlloyDBService()

