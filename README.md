# Nimap Financial Document API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC244C?style=for-the-badge)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)

A production-grade **Financial Document Management API** with **semantic search** powered by a RAG (Retrieval-Augmented Generation) pipeline, **Role-Based Access Control**, and full **Docker** orchestration.

---

## Table of Contents

- [Architecture](#architecture)
- [Infrastructure & Service URLs](#infrastructure--service-urls)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
- [Changing User Roles](#changing-user-roles)
- [API Reference](#api-reference)
  - [Health Check](#health-check)
  - [Authentication](#authentication)
  - [Users & Roles](#users--roles)
  - [Documents](#documents)
  - [RAG Pipeline](#rag-pipeline)
- [RAG Pipeline Deep Dive](#rag-pipeline-deep-dive)
- [Project Structure](#project-structure)
- [Utility Scripts](#utility-scripts)
- [Troubleshooting](#troubleshooting)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client (Swagger / curl)                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  HTTP + JWT Bearer Token
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application (:8000)                    │
│                                                                     │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐  │
│  │ Auth API │  │ Documents API│  │  Users API │  │   RAG API    │  │
│  └────┬─────┘  └──────┬───────┘  └─────┬──────┘  └──────┬───────┘  │
│       │               │               │                 │          │
│       ▼               ▼               ▼                 ▼          │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                  Security Layer (JWT + RBAC)                │    │
│  └─────────────────────────────────────────────────────────────┘    │
└───────┬────────────────┬────────────────────────────┬──────────────┘
        │                │                            │
        ▼                ▼                            ▼
┌──────────────┐  ┌─────────────┐        ┌──────────────────────────┐
│ PostgreSQL   │  │ Local Disk  │        │    RAG Pipeline          │
│ (:5432)      │  │ (uploads/)  │        │                          │
│              │  │             │        │  PDF Extract → Chunk     │
│ • Users      │  │ • PDF files │        │       → Embed → Store    │
│ • Roles      │  │ • TXT files │        │                          │
│ • Documents  │  │             │        │  Query → Retrieve(Top20) │
│ • UserRoles  │  │             │        │       → Rerank → Top 5   │
└──────────────┘  └─────────────┘        └────────────┬─────────────┘
                                                      │
                                                      ▼
                                          ┌──────────────────────┐
                                          │  Qdrant Vector DB    │
                                          │  (:6333 / :6334)     │
                                          │                      │
                                          │  Collection:         │
                                          │  financial_docs      │
                                          │  (384-dim, Cosine)   │
                                          └──────────────────────┘
```

---

## Infrastructure & Service URLs

Once the stack is running, these are the live dashboards and tools:

| Service | URL | What It's For |
| :--- | :--- | :--- |
| **FastAPI – Swagger UI** | http://localhost:8000/docs | Interactive API documentation. Test every endpoint directly from the browser, authenticate with JWT, and inspect request/response schemas. |
| **FastAPI – ReDoc** | http://localhost:8000/redoc | Alternative read-only API documentation with a cleaner layout. |
| **FastAPI – Health** | http://localhost:8000/health | Quick liveness probe — returns `{"status": "ok"}` if the API is running. |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Visual interface for the vector database. Inspect the `financial_docs` collection, view stored points, check collection health, and browse vector payloads. |
| **Qdrant REST API** | http://localhost:6333 | Direct REST access to Qdrant. Useful for debugging — e.g. `GET http://localhost:6333/collections/financial_docs` to check point count. |
| **Qdrant gRPC** | localhost:6334 | High-performance gRPC endpoint for Qdrant (used internally by the client library). |
| **pgAdmin 4** | http://localhost:5050 | Full-featured PostgreSQL admin panel. Use it to browse tables, run SQL queries, and inspect data. Login with the credentials set in your `.env` (`PG_ADMIN_EMAIL` / `PG_ADMIN_PASSWORD`). |
| **PostgreSQL** | localhost:5432 | Direct database access for tools like `psql`, DBeaver, or DataGrip. |

---

## Getting Started

### Prerequisites
- **Docker** & **Docker Compose** (v2+)
- **Git**

### 1. Clone & Configure
```bash
git clone https://github.com/once27/nimap_assignment.git
cd nimap_assignment

# Create your environment file from the template
cp .env.example .env
# Edit .env and set your secrets (SECRET_KEY, DB credentials, pgAdmin creds)
```

### 2. Launch the Full Stack
```bash
docker compose up -d --build
```
This starts **4 containers**: FastAPI app, PostgreSQL, Qdrant, and pgAdmin.

### 3. Initialize the Database
```bash
# Apply all database migrations
docker compose exec app alembic upgrade head

# Seed the 4 system roles (Admin, Financial Analyst, Auditor, Client)
docker compose exec app python app/seed.py
```

### 4. Verify
- Open http://localhost:8000/docs — you should see the Swagger UI.
- Open http://localhost:6333/dashboard — the Qdrant dashboard should load.

---

## Environment Variables

Create a `.env` file in the project root (see `.env.example`):

| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/nimap_db` |
| `SECRET_KEY` | JWT signing secret | `your-secret-key-here` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry duration | `15` |
| `QDRANT_HOST` | Qdrant hostname | `localhost` (or `qdrant` inside Docker) |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `POSTGRES_DB` | Database name | `nimap_db` |
| `PG_ADMIN_EMAIL` | pgAdmin login email | `admin@nimap.com` |
| `PG_ADMIN_PASSWORD` | pgAdmin login password | `admin` |

> **Note:** Inside Docker Compose, the app container uses `DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}` and `QDRANT_HOST=qdrant` automatically via the compose override.

---

## Role-Based Access Control (RBAC)

The system has **4 roles**, seeded by `app/seed.py`:

| Role | Permissions | What They Can Do |
| :--- | :--- | :--- |
| **Admin** | `*` (wildcard) | Full system access. Can bypass all role checks. Can assign roles to other users. |
| **Financial Analyst** | `upload_doc`, `edit_doc`, `search_doc` | Upload documents, trigger RAG indexing, remove embeddings, perform semantic search. |
| **Auditor** | `view_doc`, `search_doc` | Read-only access to documents and search results. Can view document context. |
| **Client** | `view_doc`, `search_doc` | View own documents and search. Clients with a `company_name` automatically search across their entire company's documents. |

> **Default Role:** Every new user registered via `/auth/register` is automatically assigned the **Client** role.

> **Admin Bypass:** The `Admin` role automatically passes every role check in the system — no endpoint is restricted from an Admin.

---

## Changing User Roles

There are **two ways** to change a user's role:

### Method 1: CLI Script (No API auth needed)

The `scripts/change_role.py` script directly modifies the database. Useful for bootstrapping your first Admin user.

```bash
# Syntax
docker compose exec app python scripts/change_role.py <username> <role_name>

# Examples
docker compose exec app python scripts/change_role.py popeye Admin
docker compose exec app python scripts/change_role.py john "Financial Analyst"
docker compose exec app python scripts/change_role.py jane Auditor
docker compose exec app python scripts/change_role.py bob Client
```

**How it works:**
1. Looks up the user by `username` in PostgreSQL.
2. Looks up the role by `role_name` in the roles table.
3. Replaces the user's current role(s) with the new one.
4. Prints success/failure to the terminal.

**Error cases:**
- `Error: User 'xyz' not found.` — the username doesn't exist.
- `Error: Role 'xyz' not found.` — the role name doesn't match any seeded role. Use exact names: `Admin`, `Financial Analyst`, `Auditor`, `Client`.

### Method 2: API Endpoint (Requires Admin token)

```
POST /users/assign-role
Authorization: Bearer <admin_jwt_token>
```
```json
{
    "username": "john",
    "role_name": "Financial Analyst"
}
```

---

## API Reference

All endpoints require a **Bearer token** (obtained from `/auth/login`) unless noted otherwise. Pass it as:
```
Authorization: Bearer <your_token>
```

---

### Health Check

| Endpoint | Method | Auth | Description |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | None | Returns `{"status": "ok", "message": "API is up and running!"}` |

---

### Authentication

#### `POST /auth/register` — Create a New Account

No authentication required.

**Request Body (JSON):**
```json
{
    "username": "popeye",
    "email": "popeye@example.com",
    "password": "strongpassword123",
    "company_name": "Acme Corp"
}
```

| Field | Type | Required | Validation |
| :--- | :--- | :--- | :--- |
| `username` | string | ✅ | Alphanumeric only (`^[a-zA-Z0-9]+$`) |
| `email` | string | ✅ | Valid email format |
| `password` | string | ✅ | — |
| `company_name` | string | ❌ | Optional. Links the user to a company for scoped search. |

**Response** (`201 Created`):
```json
{
    "id": "uuid",
    "username": "popeye",
    "email": "popeye@example.com",
    "is_active": true,
    "created_at": "2026-04-17T10:00:00"
}
```

> The user is automatically assigned the **Client** role upon registration.

---

#### `POST /auth/login` — Obtain JWT Token

No authentication required.

**Request Body (JSON):**
```json
{
    "username_or_email": "popeye",
    "password": "strongpassword123"
}
```

| Field | Type | Required | Notes |
| :--- | :--- | :--- | :--- |
| `username_or_email` | string | ✅ | Accepts either username or email |
| `password` | string | ✅ | — |

**Response** (`200 OK`):
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

> Token expires after **15 minutes** by default (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

---

### Users & Roles

| Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `POST /users/assign-role` | `POST` | **Admin** | Assign a role to any user |
| `GET /users/me/roles` | `GET` | Any authenticated | Get your current role(s) |
| `GET /users/me/permissions` | `GET` | Any authenticated | Get your permission list |
| `GET /users/roles` | `GET` | **Admin** | List all system roles |

#### `POST /users/assign-role`

**Request Body (JSON):**
```json
{
    "username": "john",
    "role_name": "Financial Analyst"
}
```

**Response** (`200 OK`):
```json
{
    "status": "success",
    "message": "User john is now Financial Analyst"
}
```

---

### Documents

All document endpoints require authentication. Users can only access their own documents.

#### `POST /documents/upload` — Upload a Document

**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
| :--- | :--- | :--- | :--- |
| `file` | File | ✅ | PDF or TXT file |
| `company_name` | string | ❌ | e.g. `"Acme Corp"` |
| `document_type` | string | ❌ | e.g. `"invoice"`, `"report"`, `"contract"` |

**Response** (`201 Created`):
```json
{
    "id": "uuid",
    "title": "report.pdf",
    "company_name": "Acme Corp",
    "document_type": "report",
    "file_path": "uploads/abc123.pdf",
    "file_hash": "sha256...",
    "status": "pending",
    "upload_date": "2026-04-17T10:00:00",
    "owner_id": "uuid"
}
```

> **Deduplication:** If a file with the same SHA256 hash already exists, the API returns the existing record instead of creating a duplicate.

---

#### `GET /documents/` — List My Documents

Returns all documents owned by the authenticated user.

**Response** (`200 OK`): Array of `DocumentResponse` objects.

---

#### `GET /documents/search` — Search by Metadata

Filters documents by metadata fields. All filters are optional and combined with AND logic.

| Query Param | Type | Description |
| :--- | :--- | :--- |
| `title` | string | Partial match (case-insensitive) |
| `company_name` | string | Partial match (case-insensitive) |
| `document_type` | string | Exact match |

**Example:** `GET /documents/search?company_name=Acme&document_type=invoice`

---

#### `GET /documents/{identifier}` — Get Document by ID or Title

The `identifier` can be:
- A **UUID** — exact match on document ID.
- A **string** — partial, case-insensitive match on document title (returns most recent match).

---

#### `DELETE /documents/{identifier}` — Delete a Document

Same smart identifier logic. Deletes the document record from the database **and** removes the file from disk.

**Response:** `204 No Content`

---

### RAG Pipeline

#### `POST /rag/index-document` — Index Documents for Semantic Search

**Role Required:** `Financial Analyst` (or `Admin`)

Triggers background processing: **PDF text extraction → paragraph chunking → embedding generation → Qdrant storage**.

| Query Param | Required | Behavior |
| :--- | :--- | :--- |
| `identifier` | ❌ | If provided (UUID or partial title): index that single document. If omitted: bulk-index all `pending` and `failed` documents. |

**Example — Single document:**
```
POST /rag/index-document?identifier=annual_report
```

**Example — Bulk index all pending:**
```
POST /rag/index-document
```

**Response** (`202 Accepted`):
```json
{
    "message": "Started indexing 3 document(s) in the background.",
    "documents": ["report.pdf", "invoice.pdf", "contract.pdf"],
    "status": "processing"
}
```

> Document status transitions: `pending` → `processing` → `ready` (or `failed` on error).

---

#### `POST /rag/search` — Semantic Search

**Role Required:** Any authenticated user

Performs a **two-stage retrieval** across your indexed documents:

**Request Body (JSON):**
```json
{
    "query": "What were the quarterly revenue figures?"
}
```

**Response** (`200 OK`):
```json
{
    "query": "What were the quarterly revenue figures?",
    "results": [
        {
            "text": "The quarterly revenue for Q3 was $2.4M...",
            "document_id": "uuid",
            "document_title": "annual_report.pdf",
            "score": 4.82,
            "chunk_index": 7
        }
    ],
    "message": "Successfully retrieved 5 relevant results."
}
```

> **Client scope:** Users with the `Client` role and a `company_name` automatically search across **all documents belonging to their company**, not just their own.

---

#### `GET /rag/context/{identifier}` — View Document Chunks

**Role Required:** `Admin`, `Financial Analyst`, `Auditor`, or `Client`

Retrieves all indexed text chunks for a specific document. Useful for inspecting what was extracted and how it was chunked.

The `identifier` accepts a UUID or partial document title.

**Response** (`200 OK`):
```json
{
    "document_id": "uuid",
    "chunks": [
        {
            "text": "First paragraph of the document...",
            "chunk_index": 0,
            "metadata": {
                "title": "report.pdf",
                "document_type": "report",
                "company_name": "Acme Corp"
            }
        }
    ],
    "total_chunks": 12
}
```

> **Security:** Non-admin users can only view chunks for documents they own.

---

#### `DELETE /rag/remove-document` — Remove Embeddings

**Role Required:** `Financial Analyst` (or `Admin`)

| Path/Param | Behavior |
| :--- | :--- |
| `DELETE /rag/remove-document/{id}` | Remove all vectors for a specific document (by UUID). Resets its status back to `pending`. |
| `DELETE /rag/remove-document` | **Orphan cleanup** — automatically purges vectors for documents that no longer exist in your account. |

---

## RAG Pipeline Deep Dive

### How Indexing Works

When you call `POST /rag/index-document`, the system processes each document in the background:

```
PDF/TXT File
    │
    ▼
┌──────────────────────┐
│  1. Text Extraction   │  pdfplumber (PDF) or direct read (TXT)
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  2. Chunking          │  Paragraph-based splitting
│                       │  Max size: 512 chars
│                       │  Overlap: 50 chars
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  3. Embedding         │  Model: all-MiniLM-L6-v2
│                       │  Output: 384-dimensional vectors
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  4. Vector Storage    │  Qdrant collection: financial_docs
│                       │  Distance metric: Cosine Similarity
│                       │  Payload: text, document_id, owner_id,
│                       │           company_name, document_type
└──────────────────────┘
```

### How Search Works

Semantic search uses a **two-stage retrieval** pipeline for high accuracy:

```
User Query: "What were the revenue figures?"
    │
    ▼
┌──────────────────────────────────────────┐
│  Stage 1: Bi-Encoder Retrieval           │
│  Model: all-MiniLM-L6-v2                │
│  • Encodes query into 384-dim vector     │
│  • Cosine similarity search in Qdrant    │
│  • Fetches Top 20 candidates             │
│  • Filters below threshold (score < 0.3) │
└──────────────────┬───────────────────────┘
                   ▼
┌──────────────────────────────────────────┐
│  Stage 2: Cross-Encoder Reranking        │
│  Model: ms-marco-MiniLM-L-6-v2          │
│  • Evaluates each (query, chunk) pair    │
│  • Produces precision relevance scores   │
│  • Filters below threshold (< -5.0)     │
│  • Sorts by score descending             │
│  • Returns Top 5 results                 │
└──────────────────────────────────────────┘
```

---

## Project Structure

```
nimap_assignment/
├── app/
│   ├── main.py                 # FastAPI app entrypoint & router registration
│   ├── seed.py                 # Seeds the 4 system roles into the database
│   ├── api/
│   │   ├── auth.py             # /auth endpoints (register, login)
│   │   ├── users.py            # /users endpoints (roles, permissions)
│   │   ├── documents.py        # /documents endpoints (CRUD, search)
│   │   ├── rag.py              # /rag endpoints (index, search, context)
│   │   └── deps.py             # Auth dependencies (JWT decode, role checks)
│   ├── core/
│   │   ├── config.py           # Pydantic settings (env vars)
│   │   ├── security.py         # Password hashing & JWT creation
│   │   └── logger.py           # Centralized logging setup
│   ├── models/
│   │   ├── user.py             # User SQLAlchemy model
│   │   ├── role.py             # Role & UserRole models
│   │   └── document.py         # Document model
│   ├── schemas/
│   │   ├── auth.py             # Register/Login/Token schemas
│   │   ├── user.py             # User response schema
│   │   ├── role.py             # Role response schema
│   │   ├── document.py         # Document response schema
│   │   └── rag.py              # Search/Context request & response schemas
│   ├── services/
│   │   ├── pdf_service.py      # Text extraction (PDF via pdfplumber, TXT)
│   │   ├── embedding_service.py # Bi-Encoder & Cross-Encoder model wrapper
│   │   ├── vector_db_service.py # Qdrant client (upsert, search, cleanup)
│   │   └── search_service.py   # Two-stage retrieval + reranking logic
│   ├── utils/
│   │   └── chunking.py         # Paragraph-based text chunking
│   └── db/
│       ├── base.py             # SQLAlchemy declarative base
│       └── session.py          # DB session factory
├── alembic/                    # Database migration scripts
├── alembic.ini                 # Alembic configuration
├── scripts/
│   ├── change_role.py          # CLI tool to change user roles
│   └── reset_qdrant.py         # CLI tool to reset the Qdrant collection
├── uploads/                    # Uploaded files stored here
├── docker-compose.yml          # Multi-container orchestration (4 services)
├── Dockerfile                  # Python 3.10-slim based image
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
└── .gitignore
```

---

## Utility Scripts

### `scripts/change_role.py`
Change a user's role directly from the terminal (no API auth needed).

```bash
docker compose exec app python scripts/change_role.py <username> <role_name>
```

| Argument | Description | Valid Values |
| :--- | :--- | :--- |
| `username` | The target user's username | Any registered username |
| `role_name` | The role to assign | `Admin`, `Financial Analyst`, `Auditor`, `Client` |

### `scripts/reset_qdrant.py`
Deletes the entire `financial_docs` collection from Qdrant. The collection is automatically recreated on the next indexing operation.

```bash
docker compose exec app python scripts/reset_qdrant.py
```

> **Use this when:** Qdrant data is corrupted, vector dimensions changed, or you want a completely fresh vector index.

---

## Troubleshooting

### Search returns empty results after restarting containers
The Qdrant data volume may have been lost. Re-index your documents:
```bash
# Reset the vector collection
docker compose exec app python scripts/reset_qdrant.py

# Reset all document statuses to "pending" so they can be re-indexed
docker compose exec db psql -U postgres -d nimap_db -c "UPDATE documents SET status = 'pending';"

# Then trigger bulk indexing via the API (as a Financial Analyst or Admin)
# POST http://localhost:8000/rag/index-document
```

### Database migration errors
```bash
# Check current migration state
docker compose exec app alembic current

# Force upgrade to latest
docker compose exec app alembic upgrade head
```

### Viewing logs
```bash
# All services
docker compose logs -f

# Just the app
docker compose logs -f app
```

### Connecting to PostgreSQL directly
```bash
docker compose exec db psql -U postgres -d nimap_db
```

---

*Built for the Nimap Technologies Technical Assignment.*
