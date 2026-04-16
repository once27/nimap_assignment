from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api import auth, users, documents, rag
from app.core.logger import setup_logger

logger = setup_logger("nimap_main")

app = FastAPI(
    title="Nimap Assignment",
    description="FastAPI Financial Document Management with Semantic Analysis",
    version="1.0.0",
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled system crash at {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check logs or contact support."}
    )

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(rag.router)

@app.get("/health", tags=["Health"])
def health_check():
    """
    Basic health check endpoint to verify the API is running.
    """
    return {"status": "ok", "message": "API is up and running!"}
