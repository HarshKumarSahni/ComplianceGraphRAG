import json
import re
from typing import Dict, Any, Tuple
from pydantic import ValidationError
from app.schemas.knowledge_extraction import ExtractionLLMOutput
from app.core.logger import logger


class JSONValidator:
    @staticmethod
    def _attempt_repair(raw_str: str) -> str:
        """
        Attempt to repair common LLM JSON truncation issues:
        - Truncated mid-string (Unterminated string)
        - Missing closing brackets/braces
        """
        s = raw_str.strip()

        # Remove trailing commas before closing brackets (common LLM mistake)
        s = re.sub(r",\s*([\]\}])", r"\1", s)

        # If string ends mid-value, truncate to last complete top-level key safely
        # Count braces and brackets, add missing closers
        open_braces = s.count("{") - s.count("}")
        open_brackets = s.count("[") - s.count("]")

        # Close any unclosed string (find last unescaped quote imbalance)
        # Simple heuristic: if inside a string (odd number of unescaped quotes after last { or [)
        # just close it with a quote
        try:
            json.loads(s)
            return s  # Already valid
        except json.JSONDecodeError as e:
            if "Unterminated string" in str(e) or "Expecting" in str(e):
                # Trim to error position and close open structures
                pos = e.pos if hasattr(e, "pos") else len(s)
                s = s[:pos].rstrip().rstrip(",")

                # Close any open string
                in_string = False
                escape_next = False
                for ch in s:
                    if escape_next:
                        escape_next = False
                        continue
                    if ch == "\\":
                        escape_next = True
                        continue
                    if ch == '"':
                        in_string = not in_string
                if in_string:
                    s += '"'

                # Re-count and close open structures
                open_braces = s.count("{") - s.count("}")
                open_brackets = s.count("[") - s.count("]")

        # Close open arrays first, then objects
        s += "]" * max(0, open_brackets)
        s += "}" * max(0, open_braces)

        return s

    @staticmethod
    def validate_llm_json(raw_json: Dict[str, Any]) -> Tuple[bool, ExtractionLLMOutput, str]:
        """Validate and coerce LLM JSON output into ExtractionLLMOutput schema."""
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

    @staticmethod
    def repair_and_validate(raw_str: str) -> Tuple[bool, ExtractionLLMOutput, str]:
        """
        Attempt JSON repair on a raw string, then validate.
        Returns (success, output, error_message).
        """
        try:
            repaired = JSONValidator._attempt_repair(raw_str)
            parsed = json.loads(repaired)
            return JSONValidator.validate_llm_json(parsed)
        except Exception as e:
            error_msg = f"JSON repair failed: {str(e)}"
            logger.warning(error_msg)
            return False, ExtractionLLMOutput(), error_msg
