"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel, Field, conlist
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SewingSentense(BaseModel):
    """Represents a parsed sewing instruction sentence."""
    action: str = Field(
        description="Sentence with subject, predicate and object, describing an action of sewing instruction"
    )
    subject: str = Field(description="A subject of sewing instruction")
    predicat: str = Field(description="A predicate of sewing instruction")
    object_: str = Field(description="An object of sewing instruction")


class ImageWithText(BaseModel):
    """Represents an instruction with associated image bounding box."""
    page: int = Field(description="Page number")
    header: str = Field(description="Section header")
    instruction: str = Field(description="Text with steps of sewing instruction")
    box_2d: conlist(item_type=int, min_length=4, max_length=4) = Field(
        description="The bounding box of the image that best fits the instruction [y1, x1, y2, x2]"
    )


class Instructions(BaseModel):
    """Complete structured tutorial extracted from PDF."""
    title: str = Field(description="Name of the garment")
    brief: str = Field(description="Description of garment")
    specifications: str = Field(description="Specifications of garment")
    production_package: str = Field(
        description="Supplying, equipment and materials of garment",
        default=''
    )
    fabric_consumption: str = Field(
        description="Fabric consumption of garment",
        default=''
    )
    preprocessings: str = Field(
        description="All pre-processings required before starting sewing",
        default=''
    )
    list_instructions: List[ImageWithText] = Field(
        description="List of instruction steps with associated images"
    )


# API Request/Response Models

class DocumentCreate(BaseModel):
    """Request model for creating a document."""
    filename: str
    title: str
    brief: Optional[str] = None
    specifications: Optional[str] = None
    production_package: Optional[str] = None
    fabric_consumption: Optional[str] = None
    preprocessings: Optional[str] = None


class DocumentResponse(BaseModel):
    """Response model for document."""
    id: UUID
    filename: str
    title: str
    brief: Optional[str]
    specifications: Optional[str]
    production_package: Optional[str]
    fabric_consumption: Optional[str]
    preprocessings: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InstructionResponse(BaseModel):
    """Response model for instruction."""
    id: UUID
    parent_id: UUID
    page: int
    header: str
    instruction: str
    box_2d: List[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessDocumentRequest(BaseModel):
    """Request model for processing a document from Google Drive."""
    file_id: Optional[str] = Field(None, description="Google Drive file ID")
    filename: Optional[str] = Field(None, description="Filename to process (if file_id not provided)")


class SearchRequest(BaseModel):
    """Request model for vector similarity search."""
    query: str = Field(description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    search_type: str = Field(default="documents", description="Type of search: 'documents' or 'instructions'")


class SearchResult(BaseModel):
    """Response model for search result."""
    id: UUID
    similarity: float
    title: Optional[str] = None
    brief: Optional[str] = None
    header: Optional[str] = None
    instruction: Optional[str] = None
    page: Optional[int] = None


class DocumentWithInstructions(BaseModel):
    """Response model for document with all its instructions."""
    document: DocumentResponse
    instructions: List[InstructionResponse]

