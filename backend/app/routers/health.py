from fastapi import APIRouter, Depends
from app.schemas.health import HealthResponse
from app.core.config import get_settings, Settings
from app.dependencies.providers import get_neo4j_client
from app.dependencies.clients import Neo4jClient

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),
    neo4j_client: Neo4jClient = Depends(get_neo4j_client)
):
    cloudinary_service = CloudinaryService(settings)
    cloudinary_status = cloudinary_service.check_health()

    openrouter_client = OpenRouterClient(settings)
    openrouter_status = openrouter_client.check_health()

    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version="1.0.0-knowledge-extraction",
        services={
            "api": "online",
            "neo4j": "connected",
            "cloudinary": cloudinary_status,
            "openrouter": openrouter_status
        }
    )
