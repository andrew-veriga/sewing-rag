# API Specification

## 1. Base URL
All endpoints are prefixed with `/api`.
Local Development: `http://localhost:8000/api`

## 2. Endpoints

### 2.1 Documents

#### Process Document
Process a PDF document from Google Drive or local upload.
- **URL**: `/documents/process`
- **Method**: `POST`
- **Body**:
```json
{
  "file_id": "1abc...",    // Optional: Drive File ID
  "filename": "file.pdf"   // Optional: Filename if local
}
```
- **Response**: `200 OK`
```json
{
  "id": "uuid...",
  "filename": "file.pdf",
  "title": "Extracted Title",
  "status": "processed" 
}
```

#### Batch Process
Trigger processing for multiple files in the configured Drive folder.
- **URL**: `/documents/batch-process`
- **Method**: `POST`
- **Response**: `202 Accepted`
```json
{
  "message": "Batch processing started",
  "task_id": "..."
}
```

#### List Documents
Get a list of all processed documents.
- **URL**: `/documents`
- **Method**: `GET`
- **Response**: `200 OK`
```json
[
  {
    "id": "uuid...",
    "filename": "file.pdf",
    "title": "Title",
    "created_at": "2023-10-27T10:00:00Z"
  }
]
```

#### Get Document Details
Get full details for a document, including instructions.
- **URL**: `/documents/{doc_id}`
- **Method**: `GET`
- **Response**: `200 OK`
```json
{
  "document": {
    "id": "uuid...",
    "title": "Title",
    "specifications": "..."
  },
  "instructions": [
    {
      "id": "uuid...",
      "page": 1,
      "header": "Step 1",
      "instruction": "Do this...",
      "box_2d": [100, 100, 200, 200]
    }
  ]
}
```

#### Delete Document
Remove a document and its embeddings from the database.
- **URL**: `/documents/{doc_id}`
- **Method**: `DELETE`
- **Response**: `204 No Content`

### 2.2 Search

#### Vector Search
Perform a semantic search across documents or instructions.
- **URL**: `/documents/search`
- **Method**: `POST`
- **Body**:
```json
{
  "query": "how to sew a zipper",
  "limit": 5,
  "search_type": "instructions" // or "documents"
}
```
- **Response**: `200 OK`
```json
[
  {
    "id": "uuid...",
    "similarity": 0.85,
    "instruction": "Place the zipper...",
    "document_title": "Pants Pattern"
  }
]
```

### 2.3 System / Drive

#### List Drive Files
List PDF files available in the configured Google Drive folder.
- **URL**: `/drive/files`
- **Method**: `GET`
- **Response**: `200 OK`
```json
[
  {
    "id": "1abc...",
    "name": "pattern.pdf",
    "mimeType": "application/pdf"
  }
]
```
