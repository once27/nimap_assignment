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

### Smart Identifiers
Endpoints like `GET /documents/{identifier}`, `DELETE /documents/{identifier}`, and `POST /rag/index-document/{identifier}` are designed for maximum efficiency:
- **UUID Support**: If a valid UUID is provided, the system performs a precise lookup by ID.
- **Partial Name Matching**: If a string is provided (e.g., `My bio`), the system performs a case-insensitive partial match against document titles. You don't need to type the full filename or extension.
- **Tie-Breaking**: If multiple documents match a partial name, the system automatically targets the **most recently uploaded** one.
- **Ownership**: All operations are strictly restricted to the owner of the document.

