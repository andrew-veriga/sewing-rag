# Database Schema

## 1. Overview
The database is built on **AlloyDB Omni** (PostgreSQL-compatible) and utilizes the following extensions:
- `vector`: For storing and querying high-dimensional vector embeddings.
- `google_ml_integration`: For integration with Vertex AI (generating embeddings).

## 2. Tables

### 2.1 `documents`
Stores metadata and full-text summaries of processed PDF documents.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `UUID` (PK) | Unique identifier (auto-generated) |
| `filename` | `VARCHAR(255)` | Original filename (Unique) |
| `title` | `TEXT` | Extracted title of the document |
| `brief` | `TEXT` | Brief description/summary |
| `specifications` | `TEXT` | Technical specifications |
| `production_package` | `TEXT` | Details on equipment/materials |
| `fabric_consumption` | `TEXT` | Fabric usage details |
| `preprocessings` | `TEXT` | Pre-sewing instructions |
| `embedding` | `vector(768)` | Semantic embedding of the document content |
| `created_at` | `TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMP` | Last update timestamp |

### 2.2 `instructions`
Stores individual instruction steps extracted from the documents.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `UUID` (PK) | Unique identifier |
| `parent_id` | `UUID` (FK) | Reference to `documents.id` |
| `page` | `INTEGER` | Page number in the original PDF |
| `header` | `TEXT` | Section header for the step |
| `instruction` | `TEXT` | The instruction text |
| `box_2d` | `INTEGER[4]` | Bounding box [y1, x1, y2, x2] |
| `embedding` | `vector(768)` | Semantic embedding of the instruction |
| `created_at` | `TIMESTAMP` | Creation timestamp |

## 3. Relationships
- **One-to-Many**: `documents` (1) -> `instructions` (N)
  - `instructions.parent_id` references `documents.id` with `ON DELETE CASCADE`.

## 4. Indexes

### 4.1 Vector Search Indexes (ScaNN)
Optimized for Approximate Nearest Neighbor (ANN) search.
- `idx_documents_embedding_scann`: On `documents(embedding)`
- `idx_instructions_embedding_scann`: On `instructions(embedding)`
- **Configuration**: `num_leaves = 100`, `num_leaves_to_search = 10`

### 4.2 Text Search Indexes (GIN)
Optimized for full-text search.
- `idx_documents_title`
- `idx_documents_brief`
- `idx_instructions_header`
- `idx_instructions_instruction`

### 4.3 Standard Indexes
- `idx_documents_filename` (Unique)
- `idx_instructions_parent_id` (FK lookup)
- `idx_instructions_page`
