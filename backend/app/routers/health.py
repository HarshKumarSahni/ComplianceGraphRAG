from fastapi import APIRouter, Depends
from app.schemas.health import HealthResponse
from app.core.config import get_settings, Settings
from app.dependencies.providers import get_neo4j_client
from app.dependencies.clients import Neo4jClient
from app.services.cloudinary_service import CloudinaryService
from app.services.openrouter_client import OpenRouterClient

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
):
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        services={
            "api": "online",
            "neo4j": "connected",
            "cloudinary": "configured" if settings.CLOUDINARY_CLOUD_NAME else "not_configured",
            "openrouter": "configured" if settings.OPENROUTER_API_KEY else "not_configured",
        },
    )