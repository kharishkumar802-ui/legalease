from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.routes import router


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered legal document "
        "drafting and export API."
    ),
    version="1.0.0",
)


# =================================================
# CORS
# =================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],

    allow_credentials=False,

    allow_methods=[
        "GET",
        "POST",
    ],

    allow_headers=[
        "Content-Type",
    ],
)


# =================================================
# ROOT
# =================================================

@app.get("/")
def root():

    return {
        "name": settings.app_name,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# =================================================
# ROUTES
# =================================================

app.include_router(
    router
)