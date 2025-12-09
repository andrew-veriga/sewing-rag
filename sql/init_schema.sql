-- Active: 1764839619516@@88.218.76.58@5432@pdf_understanding
-- AlloyDB Schema for PDF2AlloyDB Application
-- This schema stores extracted PDF document data with vector embeddings

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS google_ml_integration;

-- Documents table (parent records)
-- Stores the main document metadata and aggregated information
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    brief TEXT,
    specifications TEXT,
    production_package TEXT,
    fabric_consumption TEXT,
    preprocessings TEXT,
    -- Vector embedding for the entire document (concatenated fields)
    embedding vector(768), -- text-embedding-004 produces 768-dimensional vectors
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Indexes for text search
    CONSTRAINT documents_filename_unique UNIQUE (filename)
);

-- Instructions table (child records)
-- Stores individual instruction steps with their associated images and bounding boxes
CREATE TABLE IF NOT EXISTS instructions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page INTEGER NOT NULL,
    header TEXT NOT NULL,
    instruction TEXT NOT NULL,
    -- Bounding box coordinates: [y1, x1, y2, x2] in normalized format (0-1000)
    box_2d INTEGER[4] NOT NULL,
    -- Vector embedding for this instruction
    embedding vector(768),
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Indexes
    CONSTRAINT instructions_box_2d_length CHECK (array_length(box_2d, 1) = 4)
);

-- Create indexes for efficient querying

-- Text search indexes on documents
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_documents_title ON documents USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_documents_brief ON documents USING gin(to_tsvector('english', brief));

-- Text search indexes on instructions
CREATE INDEX IF NOT EXISTS idx_instructions_parent_id ON instructions(parent_id);
CREATE INDEX IF NOT EXISTS idx_instructions_page ON instructions(page);
CREATE INDEX IF NOT EXISTS idx_instructions_header ON instructions USING gin(to_tsvector('english', header));
CREATE INDEX IF NOT EXISTS idx_instructions_instruction ON instructions USING gin(to_tsvector('english', instruction));

-- Vector similarity search indexes using ScaNN (AlloyDB's optimized vector index)
-- For documents table
CREATE INDEX IF NOT EXISTS idx_documents_embedding_scann 
ON documents 
USING scann (embedding vector_cosine_ops)
WITH (num_leaves = 100, num_leaves_to_search = 10);

-- For instructions table
CREATE INDEX IF NOT EXISTS idx_instructions_embedding_scann 
ON instructions 
USING scann (embedding vector_cosine_ops)
WITH (num_leaves = 100, num_leaves_to_search = 10);

-- Composite index for parent_id and page (common query pattern)
CREATE INDEX IF NOT EXISTS idx_instructions_parent_page ON instructions(parent_id, page);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE documents IS 'Main document records extracted from PDFs with metadata and embeddings';
COMMENT ON TABLE instructions IS 'Individual instruction steps with page references and bounding boxes';
COMMENT ON COLUMN documents.embedding IS '768-dimensional vector embedding for semantic search';
COMMENT ON COLUMN instructions.embedding IS '768-dimensional vector embedding for semantic search';
COMMENT ON COLUMN instructions.box_2d IS 'Bounding box coordinates [y1, x1, y2, x2] in normalized format (0-1000)';

