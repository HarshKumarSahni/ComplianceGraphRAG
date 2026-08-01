import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Dict, Any, Optional
from app.core.config import Settings
from app.core.logger import logger
from app.core.exceptions import ExternalAPIError

class CloudinaryService:
    def __init__(self, settings: Settings):
        self.cloud_name = settings.CLOUDINARY_CLOUD_NAME
        self.api_key = settings.CLOUDINARY_API_KEY
        self.api_secret = settings.CLOUDINARY_API_SECRET
        self._is_configured = False
        self.configure()

    def configure(self):
        if self.cloud_name and self.api_key and self.api_secret:
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret,
                secure=True
            )
            self._is_configured = True
            logger.info(f"CloudinaryService configured successfully for cloud: {self.cloud_name}")
        else:
            logger.warning("Cloudinary credentials missing or incomplete. Operating in mock/test mode.")

    def check_health(self) -> str:
        if not self._is_configured:
            return "unconfigured (mock_mode)"
        try:
            # Check ping ping ping
            cloudinary.api.ping()
            return "connected"
        except Exception as e:
            logger.error(f"Cloudinary health check ping failed: {str(e)}")
            return "disconnected"

    async def upload_file_content(
        self,
        file_content: bytes,
        filename: str,
        resource_type: str = "auto"
    ) -> Dict[str, Any]:
        if not self._is_configured:
            logger.info(f"Mock Cloudinary upload executed for file: {filename}")
            return {
                "secure_url": f"https://res.cloudinary.com/mock-cloud/raw/upload/v1234567890/{filename}",
                "public_id": f"graphguard/{filename}",
                "bytes": len(file_content),
                "resource_type": resource_type
            }

        try:
            response = cloudinary.uploader.upload(
                file_content,
                public_id=f"graphguard/{filename}",
                resource_type=resource_type,
                overwrite=True
            )
            logger.info(f"Cloudinary upload successful. Public ID: {response.get('public_id')}")
            return response
        except Exception as e:
            logger.error(f"Cloudinary upload failed for {filename}: {str(e)}")
            raise ExternalAPIError(message=f"Cloudinary upload failed: {str(e)}")

    async def delete_file(self, public_id: str, resource_type: str = "raw") -> bool:
        if not self._is_configured:
            return True
        try:
            cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            return True
        except Exception as e:
            logger.error(f"Failed to delete Cloudinary asset {public_id}: {str(e)}")
            return False
