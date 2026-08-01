from typing import Dict
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    services: Dict[str, str]
