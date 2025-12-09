-- AlloyDB AI Functions for PDF2AlloyDB Application
-- These functions replace the Python GetStructuredTutorial and VectorizedTutorial logic
-- using AlloyDB's google_ml_integration extension

-- Note: PDF processing (GetStructuredTutorial) is still done in Python via Gemini API
-- These SQL functions handle embedding generation and vector operations in the database

-- Function to store a document with its embedding
-- This replaces part of VectorizedTutorial for parent documents
CREATE OR REPLACE FUNCTION store_document(
    p_filename VARCHAR(255),
    p_title TEXT,
    p_brief TEXT,
    p_specifications TEXT,
    p_production_package TEXT,
    p_fabric_consumption TEXT,
    p_preprocessings TEXT
)
RETURNS UUID AS $$
DECLARE
    doc_id UUID;
    doc_embedding vector(768);
    combined_text TEXT;
BEGIN
    -- Generate embedding from combined document fields
    combined_text := COALESCE(p_title, '') || E'\n' ||
                     COALESCE(p_brief, '') || E'\n' ||
                     COALESCE(p_specifications, '') || E'\n' ||
                     COALESCE(p_production_package, '') || E'\n' ||
                     COALESCE(p_fabric_consumption, '') || E'\n' ||
                     COALESCE(p_preprocessings, '');
    
    doc_embedding := google_ml.embedding('text-embedding-005',combined_text);
    
    -- Insert document
    INSERT INTO documents (
        filename, title, brief, specifications,
        production_package, fabric_consumption, preprocessings, embedding
    ) VALUES (
        p_filename, p_title, p_brief, p_specifications,
        p_production_package, p_fabric_consumption, p_preprocessings, doc_embedding
    )
    ON CONFLICT (filename) DO UPDATE SET
        title = EXCLUDED.title,
        brief = EXCLUDED.brief,
        specifications = EXCLUDED.specifications,
        production_package = EXCLUDED.production_package,
        fabric_consumption = EXCLUDED.fabric_consumption,
        preprocessings = EXCLUDED.preprocessings,
        embedding = EXCLUDED.embedding,
        updated_at = CURRENT_TIMESTAMP
    RETURNING id INTO doc_id;
    
    RETURN doc_id;
END;
$$ LANGUAGE plpgsql;

-- Function to store an instruction with its embedding
-- This replaces part of VectorizedTutorial for child instructions
CREATE OR REPLACE FUNCTION store_instruction(
    p_parent_id UUID,
    p_page INTEGER,
    p_header TEXT,
    p_instruction TEXT,
    p_box_2d INTEGER[4]
)
RETURNS UUID AS $$
DECLARE
    instr_id UUID;
    instr_embedding vector(768);
    instruction_text TEXT;
BEGIN
    -- Generate embedding from header and instruction
    instruction_text := 'Header: ' || COALESCE(p_header, '') || E'\n' ||
                       'Instruction: ' || COALESCE(p_instruction, '');
    
    instr_embedding := google_ml.embedding('text-embedding-005',instruction_text);
    
    -- Insert instruction
    INSERT INTO instructions (
        parent_id, page, header, instruction, box_2d, embedding
    ) VALUES (
        p_parent_id, p_page, p_header, p_instruction, p_box_2d, instr_embedding
    )
    RETURNING id INTO instr_id;
    
    RETURN instr_id;
END;
$$ LANGUAGE plpgsql;

-- Function to perform vector similarity search on documents
-- Returns documents ordered by cosine similarity
CREATE OR REPLACE FUNCTION search_documents(
    query_text TEXT,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    filename VARCHAR(255),
    title TEXT,
    brief TEXT,
    similarity FLOAT
) AS $$
DECLARE
    query_embedding vector(768);
BEGIN
    -- Generate embedding for query text
    query_embedding := google_ml.embedding('text-embedding-005',query_text);
    
    -- Perform cosine similarity search
    RETURN QUERY
    SELECT 
        d.id,
        d.filename,
        d.title,
        d.brief,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE d.embedding IS NOT NULL
    ORDER BY d.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to perform vector similarity search on instructions
-- Returns instructions ordered by cosine similarity
CREATE OR REPLACE FUNCTION search_instructions(
    query_text TEXT,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    parent_id UUID,
    page INTEGER,
    header TEXT,
    instruction TEXT,
    similarity FLOAT
) AS $$
DECLARE
    query_embedding vector(768);
BEGIN
    -- Generate embedding for query text
    query_embedding := google_ml.embedding('text-embedding-005',query_text);
    
    -- Perform cosine similarity search
    RETURN QUERY
    SELECT 
        i.id,
        i.parent_id,
        i.page,
        i.header,
        i.instruction,
        1 - (i.embedding <=> query_embedding) AS similarity
    FROM instructions i
    WHERE i.embedding IS NOT NULL
    ORDER BY i.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get all instructions for a document
CREATE OR REPLACE FUNCTION get_document_instructions(p_doc_id UUID)
RETURNS TABLE (
    id UUID,
    page INTEGER,
    header TEXT,
    instruction TEXT,
    box_2d INTEGER[4]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.page,
        i.header,
        i.instruction,
        i.box_2d
    FROM instructions i
    WHERE i.parent_id = p_doc_id
    ORDER BY i.page, i.id;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON FUNCTION store_document IS 'Stores a document with auto-generated embedding, replacing VectorizedTutorial parent document logic';
COMMENT ON FUNCTION store_instruction IS 'Stores an instruction with auto-generated embedding, replacing VectorizedTutorial child instruction logic';
COMMENT ON FUNCTION search_documents IS 'Performs semantic search on documents using vector similarity';
COMMENT ON FUNCTION search_instructions IS 'Performs semantic search on instructions using vector similarity';
COMMENT ON FUNCTION get_document_instructions IS 'Retrieves all instructions for a given document';

