# PDF2AlloyDB

A Python client-server application that processes PDF documents from Google Drive, extracts structured data using Gemini AI, generates embeddings via Vertex AI, and stores everything in AlloyDB with pgvector for vector search capabilities.

## Features

- **Google Drive Integration**: Automatically fetch and process PDF files from Google Drive
- **AI-Powered Extraction**: Uses Gemini 2.5 to extract structured data from PDFs
- **Vector Search**: Stores embeddings in AlloyDB with pgvector for semantic search
- **AlloyDB AI Functions**: Leverages AlloyDB's native AI integration for embedding generation
- **REST API**: FastAPI-based API for document processing and retrieval
- **CLI Client**: Command-line interface for interacting with the API

## Architecture

- **REST API Server** (FastAPI) - Main application server
- **Client Application** - Python client library and CLI
- **AlloyDB Database** - PostgreSQL with pgvector extension and Vertex AI integration
- **Google Drive** - Source for PDF documents

## Prerequisites

- Python 3.9+
- AlloyDB cluster with pgvector extension enabled
- Google Cloud Project with:
  - Vertex AI API enabled
  - Google Drive API enabled
  - Service account with appropriate permissions
- Poppler utilities (for PDF to image conversion)
  - Windows: Install from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)
  - Linux: `sudo apt-get install poppler-utils`
  - macOS: `brew install poppler`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd PDF2Alloydb
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/macOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Copy `.env.example` to `.env` (if available) or create `.env` file
   - Fill in all required environment variables (see Configuration section)

5. Set up AlloyDB:
   - Run the SQL scripts to initialize the database:
   ```bash
   psql -h <alloydb-host> -U <user> -d <database> -f sql/init_schema.sql
   psql -h <alloydb-host> -U <user> -d <database> -f sql/create_ai_functions.sql
   ```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Google Cloud Configuration
GOOGLE_SERVICE_CREDENTIALS=/path/to/service-account-key.json
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=us-central1

# AlloyDB Configuration
ALLOYDB_CONNECTION_STRING=postgresql://user:password@host:port/database

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=your-folder-id

# Vertex AI Configuration
VERTEX_AI_EMBEDDING_MODEL=text-embedding-004

# Gemini Configuration
GEMINI_MODEL_NAME=gemini-2.5-flash
```

## Usage

### Starting the API Server

```bash
python -m app.main
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Using the CLI Client

```bash
# Process a single document
python -m client.main process --filename "example.pdf"

# Process by file ID
python -m client.main process --file-id "1abc123..."

# Batch process all PDFs in Drive folder
python -m client.main batch-process

# List all processed documents
python -m client.main list

# Get a specific document
python -m client.main get <document-uuid>

# Search documents
python -m client.main search "sewing instructions" --type documents

# Search instructions
python -m client.main search "attach sleeve" --type instructions

# List PDFs in Google Drive
python -m client.main list-drive

# Health check
python -m client.main health
```

### API Endpoints

- `POST /api/documents/process` - Process a PDF from Google Drive
- `GET /api/documents` - List all processed documents
- `GET /api/documents/{doc_id}` - Get document details with instructions
- `POST /api/documents/search` - Vector similarity search
- `GET /api/drive/files` - List available PDFs in Google Drive
- `POST /api/documents/batch-process` - Process multiple PDFs
- `DELETE /api/documents/{doc_id}` - Delete a document

## Project Structure

```
PDF2Alloydb/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── api/
│   │   └── routes/
│   │       └── documents.py    # API endpoints
│   ├── models/
│   │   ├── schemas.py          # Pydantic models
│   │   └── database.py         # SQLAlchemy ORM models
│   ├── services/
│   │   ├── drive_service.py    # Google Drive integration
│   │   ├── pdf_service.py      # PDF processing
│   │   └── alloydb_service.py  # AlloyDB operations
│   └── db/
│       └── connection.py       # Database connection
├── client/
│   ├── api_client.py           # API client wrapper
│   ├── cli.py                  # CLI interface
│   └── main.py                 # Client entry point
├── sql/
│   ├── init_schema.sql         # Database schema
│   └── create_ai_functions.sql # AlloyDB AI functions
├── configs/
│   └── config.yaml             # Application configuration
├── auth_service.py             # Google Cloud authentication
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Development

### Running Tests

```bash
# Add tests as needed
pytest
```

### Code Style

```bash
# Format code
black .
isort .

# Lint
flake8 .
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

