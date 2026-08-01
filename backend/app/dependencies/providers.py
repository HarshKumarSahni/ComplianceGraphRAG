from typing import Generator
from app.core.config import get_settings, Settings
from app.dependencies.clients import Neo4jClient, CloudinaryClient, OpenRouterClient

def get_config() -> Settings:
    return get_settings()

def get_neo4j_client() -> Generator[Neo4jClient, None, None]:
    settings = get_settings()
    client = Neo4jClient(settings)
    client.connect()
    try:
        yield client
    finally:
        client.close()

def get_cloudinary_client() -> CloudinaryClient:
    settings = get_settings()
    client = CloudinaryClient(settings)
    client.initialize()
    return client

def get_openrouter_client() -> OpenRouterClient:
    settings = get_settings()
    client = OpenRouterClient(settings)
    client.initialize()
    return client
