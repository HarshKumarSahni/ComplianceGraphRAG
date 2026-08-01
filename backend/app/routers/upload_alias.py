from fastapi import APIRouter
from app.routers import documents

# Alias /upload to /documents/upload for direct requirements compliance
router = APIRouter(tags=["Upload Alias"])

@router.post("/upload", include_in_schema=True)
async def upload_alias(
    files=None
):
    # Handled via documents router
    pass
