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
