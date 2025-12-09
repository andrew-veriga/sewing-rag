"""SQLAlchemy ORM models for database tables."""
from sqlalchemy import Column, String, Text, Integer, ARRAY, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

Base = declarative_base()


class Document(Base):
    """ORM model for documents table."""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    brief = Column(Text)
    specifications = Column(Text)
    production_package = Column(Text)
    fabric_consumption = Column(Text)
    preprocessings = Column(Text)
    embedding = Column(Vector(768))  # 768-dimensional vector for text-embedding-004
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to instructions
    instructions = relationship("Instruction", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', title='{self.title}')>"


class Instruction(Base):
    """ORM model for instructions table."""
    __tablename__ = "instructions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page = Column(Integer, nullable=False, index=True)
    header = Column(Text, nullable=False)
    instruction = Column(Text, nullable=False)
    box_2d = Column(ARRAY(Integer), nullable=False)  # [y1, x1, y2, x2]
    embedding = Column(Vector(768))  # 768-dimensional vector for text-embedding-004
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to parent document
    document = relationship("Document", back_populates="instructions")
    
    def __repr__(self):
        return f"<Instruction(id={self.id}, parent_id={self.parent_id}, page={self.page}, header='{self.header[:50]}...')>"

