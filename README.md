# Nimap Technologies Assignment

> **FastAPI Financial Document Management with Semantic Analysis**

## Overview
A robust document management API featuring full CRUD functionality, metadata search, Role-Based Access Control (RBAC), and a Retrieval-Augmented Generation (RAG) pipeline for semantic search and reranking.

## Tech Stack
- **API**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy & Alembic
- **Auth**: JWT with python-jose & passlib
- **RAG**: sentence-transformers, Qdrant list, CrossEncoder (ms-marco-MiniLM-L-6-v2)

## Setup instructions
*(To be completed after Docker & App implementation)*

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
Endpoints like `GET /documents/{identifier}` and `DELETE /documents/{identifier}` are designed for maximum efficiency:
- **UUID Support**: If a valid UUID is provided, the system performs a precise lookup by ID.
- **Partial Name Matching**: If a string is provided (e.g., `My bio`), the system performs a case-insensitive partial match against document titles. You don't need to type the full filename or extension.
- **Tie-Breaking**: If multiple documents match a partial name, the system automatically targets the **most recently uploaded** one.
- **Ownership**: All operations are strictly restricted to the owner of the document.

