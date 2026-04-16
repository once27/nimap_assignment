from fastapi import FastAPI
from app.api import auth

app = FastAPI(
    title="Nimap Assignment",
    description="FastAPI Financial Document Management with Semantic Analysis",
    version="1.0.0",
)

app.include_router(auth.router)

@app.get("/health", tags=["Health"])
def health_check():
    """
    Basic health check endpoint to verify the API is running.
    """
    return {"status": "ok", "message": "API is up and running!"}
