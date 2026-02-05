# Requirements Specification

## 1. Introduction
PDF2AlloyDB is a system designed to automate the extraction of structured data from PDF documents (specifically sewing instructions) using Generative AI and enable semantic search capabilities using AlloyDB's vector search features.

## 2. Functional Requirements

### 2.1 Document Processing
- **FR-01**: The system MUST support fetching PDF documents directly from a configured Google Drive folder.
- **FR-02**: The system MUST support uploading PDF documents via the API.
- **FR-03**: The system MUST convert PDF pages to images for AI processing.
- **FR-04**: The system MUST use a multimodal LLM (Gemini 2.5) to extract structured data from document images, including:
  - Document metadata (Title, Brief, Specifications, etc.)
  - Step-by-step instructions with bounding boxes for relevant images.
- **FR-05**: The system MUST generate vector embeddings for:
  - The entire document summary/content.
  - Individual instruction steps.

### 2.2 Data Storage & Management
- **FR-06**: Extracted data MUST be stored in an AlloyDB database.
- **FR-07**: Vector embeddings MUST be stored using the `pgvector` extension.
- **FR-08**: The system MUST support listing, retrieving, and deleting processed documents.

### 2.3 Search & Retrieval
- **FR-09**: The system MUST support vector similarity search for entire documents.
- **FR-10**: The system MUST support vector similarity search for specific instructions.
- **FR-11**: The system MUST support filtering search results by similarity threshold and limit.

### 2.4 Client Interface
- **FR-12**: A CLI tool MUST be provided for all core operations (process, search, list).
- **FR-13**: A REST API MUST be exposed for integration with other services.

## 3. Non-Functional Requirements

### 3.1 Performance
- **NFR-01**: Vector search should utilize AlloyDB's `ScaNN` index for low-latency retrieval.
- **NFR-02**: Database queries should be optimized with appropriate text search indexes (GIN) for keyword fields.

### 3.2 Reliability & Scalability
- **NFR-03**: The system should handle Google API rate limits and transient failures gracefully (using retry logic).
- **NFR-04**: Database connection management should be efficient (connection pooling).

### 3.3 Security
- **NFR-05**: Google Cloud credentials MUST be managed securely (Service Account).
- **NFR-06**: API access should be secured (Future scope, currently open for internal use).

### 3.4 Compatibility
- **NFR-07**: The system must run on Python 3.9+.
- **NFR-08**: The system requires an AlloyDB instance with `google_ml_integration` and `vector` extensions enabled.
