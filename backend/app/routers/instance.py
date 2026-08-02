"""
DELETE /api/v1/instance

Resets the current authenticated user's entire workspace:
  - Deletes all their document records from documents_store.json
  - Deletes corresponding Cloudinary files (best-effort)
  - Deletes all their Neo4j Entity nodes, Chunk nodes, and relationships

User account (PostgreSQL) is NEVER touched.
user_id is ALWAYS taken from the JWT token — never from the request body.
"""
from fastapi import APIRouter, Depends, status
from app.schemas.response import ApiResponse
from app.core.config import get_settings, Settings
from app.dependencies.clients import Neo4jClient
from app.repositories.graph_repository import GraphRepository
from app.repositories.json_document_repository import JSONDocumentRepository
from app.services.cloudinary_service import CloudinaryService
from app.dependencies.auth_deps import get_current_user
from app.models.user import User
from app.core.logger import logger

router = APIRouter(prefix="/instance", tags=["Instance Management"])


def _get_graph_repo(settings: Settings = Depends(get_settings)) -> GraphRepository:
    client = Neo4jClient(settings)
    client.connect()
    return GraphRepository(client)


def _get_cloudinary(settings: Settings = Depends(get_settings)) -> CloudinaryService:
    return CloudinaryService(settings)


_doc_repo = JSONDocumentRepository()


@router.delete(
    "",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Reset current user's workspace",
    description=(
        "Permanently deletes all documents, Neo4j graph data, and Cloudinary files "
        "for the authenticated user. User account is preserved."
    ),
)
async def reset_instance(
    current_user: User = Depends(get_current_user),
    graph_repo: GraphRepository = Depends(_get_graph_repo),
    cloudinary_svc: CloudinaryService = Depends(_get_cloudinary),
):
    user_id = str(current_user.id)
    logger.info(f"Instance reset initiated for user {user_id}")

    # 1. Fetch documents before deletion so we have Cloudinary public_ids
    deleted_docs = await _doc_repo.delete_user_documents(user_id)
    doc_count = len(deleted_docs)

    # 2. Delete Cloudinary files (best-effort; never block the reset on Cloudinary failures)
    cloudinary_deleted = 0
    cloudinary_failed = 0
    for doc in deleted_docs:
        public_id = doc.public_id
        if not public_id or "mock" in (doc.cloudinary_url or ""):
            continue
        # Determine resource type from file_type
        resource_type = "video" if str(doc.file_type).lower() in ("audio", "mp3") else "raw"
        ok = await cloudinary_svc.delete_file(public_id, resource_type=resource_type)
        if ok:
            cloudinary_deleted += 1
        else:
            cloudinary_failed += 1

    # 3. Clear Neo4j — Entity nodes, Chunk nodes (embeddings/vectors), and all their relationships
    graph_cleared = await graph_repo.clear_graph(user_id)

    logger.info(
        f"Instance reset complete for user {user_id}: "
        f"{doc_count} docs removed, {cloudinary_deleted} Cloudinary files deleted, "
        f"Neo4j cleared={graph_cleared}"
    )

    return ApiResponse(
        success=True,
        message="New instance created. Upload files to begin.",
        data={
            "documents_deleted": doc_count,
            "cloudinary_files_deleted": cloudinary_deleted,
            "cloudinary_failures": cloudinary_failed,
            "graph_cleared": graph_cleared,
            "user_account": "preserved",
        },
    )
