# Nimap Technologies Assignment

> **FastAPI Financial Document Management with Semantic Analysis**

## Overview
A robust document management API featuring full CRUD functionality, metadata search, Role-Based Access Control (RBAC), and a Retrieval-Augmented Generation (RAG) pipeline for semantic search and reranking.

## Tech Stack
- **API**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy & Alembic
- **Auth**: JWT with python-jose & passlib
- **RAG**: sentence-transformers, Qdrant list, CrossEncoder (ms-marco-MiniLM-L-6-v2)

## Docker Infrastructure
The application is fully containerized for a production-ready setup including PostgreSQL (relational DB), Qdrant (vector DB), and PGAdmin (DB management).

### Deployment
To start the entire stack:
```bash
docker compose up -d --build
```

### Initial Setup
Once the containers are running, you must initialize the database:
1. **Run Migrations**: `alembic upgrade head`
2. **Seed Roles**: `python app/seed.py`

### Service Breakdown
| Service | URL | Note |
| :--- | :--- | :--- |
| **FastAPI Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI for testing endpoints |
| **PGAdmin** | [http://localhost:5050](http://localhost:5050) | `admin@nimap.com` / `admin` |
| **Qdrant Dashboard** | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) | Vector search health check |
| **PostgreSQL (Internal)**| `localhost:5433` | `postgres` / `postgres` |

## Authentication
- **Register**: `POST /auth/register` (Pass `username`, `email`, `password`, and optional `company_name`).
- **Login**: `POST /auth/login` (Standard JWT authentication).
- **Roles**: `Admin`, `Financial Analyst`, `Auditor`, `Client`.

## User Management
By default, all new registrations are assigned the `Client` role. 
To elevate an existing user from the terminal, activate your virtual environment and run the provided script:

```bash
# Example: Elevate a user named 'popeye' to Admin
python scripts/change_role.py popeye Admin
```
*Available Roles: `Admin`, `Analyst`, `Auditor`, `Client`*

## Document Management
The API provides a smart, unified interface for document operations.

### Document Metadata & Search
- **Upload**: `POST /documents/upload` - Accept `company_name` and `document_type` as form fields.
- **List**: `GET /documents/` - Users see their own files. **Clients** see all files for their company.
- **Metadata Search**: `GET /documents/search` - Filter repository by `title`, `company_name`, or `document_type`.

## RAG Pipeline
The RAG pipeline manages the extraction, chunking, and vector storage of your documents.

### 1. Indexing Documents (`POST /rag/index-document`)
This endpoint prepares your documents for semantic search:
- **Bulk Mode**: Call `POST /rag/index-document` with no parameters to automatically index all `pending` or `failed` documents in your account.
- **Single Mode**: Provide an `identifier` query parameter (e.g., `?identifier=My bio`) to index a specific document by ID or name.

### 2. Cleanup & Removal (`DELETE /rag/remove-document`)
- **Specific Removal**: Provide an `id` as a path parameter to remove embeddings for a specific document and reset its status to `pending`.
- **System Cleanup**: Call `DELETE /rag/remove-document` with no ID to automatically purge any "orphaned" embeddings that belong to documents you've already deleted from your main list.

### 3. Semantic Search (`POST /rag/search`)
Ask questions across the knowledge base using a **Two-Stage Pipeline**:
- **Query**: Send a JSON body with a `query` string (e.g., `{"query": "What is the return policy?"}`).
- **Harvesting**: Fast retrieval of the **Top 20** candidates using Bi-Encoder.
- **Precision Reranking**: Cross-Encoder (**ms-marco-MiniLM**) reranks results to find the most relevant answer.
- **Final Results**: Delivers the **Top 5** most relevant results.
- **Company Access**: Clients automatically search across their entire company's document base.

### 4. Document Context (`GET /rag/context/{identifier}`)
Inspect the exact chunks indexed for a document:
- **Smart Identifier**: Supports partial name (e.g., `my bio`) or UUID.
- **Full Metadata**: Shows every chunk's text, index, company name, and document type.

## Calibration & Troubleshooting
If search results appear empty after infrastructure changes:
1. **Reset Qdrant**: `docker compose exec app python scripts/reset_qdrant.py`
2. **Reset Status**: `docker compose exec db psql -U postgres -d nimap_db -c "UPDATE documents SET status = 'pending';"`
3. **Re-Index**: Run the `index-document` endpoint again in Swagger.

