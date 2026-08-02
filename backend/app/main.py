from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.logger import logger
from app.core.exceptions import BaseAppException

from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.error_handler import (
    base_app_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)

from app.db.database import engine, Base
from app.models.user import User  # Ensures User model is registered
from app.routers import health, documents, upload_alias, process, extract, query, graph, auth, instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")

def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0-foundation",
        description="GraphGuard AI - Multi-Modal Knowledge Graph Synthesis Platform Foundation",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Logging & Timing Middleware
    app.add_middleware(RequestLoggingMiddleware)

    # 3. Custom Exception Handlers
    app.add_exception_handler(BaseAppException, base_app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # 4. Include API Routers
    api_v1_str = settings.API_V1_STR
    app.include_router(health.router, prefix=api_v1_str)
    app.include_router(auth.router, prefix=api_v1_str)
    app.include_router(documents.router, prefix=api_v1_str)
    app.include_router(upload_alias.router, prefix=api_v1_str)
    app.include_router(process.router, prefix=api_v1_str)
    app.include_router(extract.router, prefix=api_v1_str)
    app.include_router(query.router, prefix=api_v1_str)
    app.include_router(graph.router, prefix=api_v1_str)
    app.include_router(instance.router, prefix=api_v1_str)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "status": "online",
            "version": "1.0.0-foundation",
            "docs": "/docs"
        }

    return app

app = create_application()
