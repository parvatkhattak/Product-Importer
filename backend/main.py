"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.config import settings
from backend.routers import products, upload, webhooks

# Create FastAPI app
app = FastAPI(
    title="Product Importer",
    description="Import products from CSV files with real-time progress tracking",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router)
app.include_router(upload.router)
app.include_router(webhooks.router)

# Serve frontend static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
