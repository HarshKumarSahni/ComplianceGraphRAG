from typing import Dict, Any, Tuple
from pydantic import ValidationError
from app.schemas.knowledge_extraction import ExtractionLLMOutput
from app.core.logger import logger

class JSONValidator:
    @staticmethod
    def validate_llm_json(raw_json: Dict[str, Any]) -> Tuple[bool, ExtractionLLMOutput, str]:
        try:
            validated_output = ExtractionLLMOutput(**raw_json)
            return True, validated_output, ""
        except ValidationError as ve:
            error_msg = f"Pydantic Validation failed: {str(ve)}"
            logger.warning(error_msg)
            return False, ExtractionLLMOutput(), error_msg
        except Exception as e:
            error_msg = f"Unexpected JSON structure error: {str(e)}"
            logger.warning(error_msg)
            return False, ExtractionLLMOutput(), error_msg
