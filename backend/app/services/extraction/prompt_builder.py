class PromptBuilder:
    @staticmethod
    def get_system_prompt() -> str:
        return """You are a strict Enterprise Compliance Knowledge Extraction Engine.
Analyze the provided text chunk and extract entities and relationships explicitly present in the text.

STRICT RULES:
1. Do NOT hallucinate. Extract only what is explicitly stated or directly implied.
2. Return ONLY valid compact JSON. No markdown, no prose, no code blocks.
3. Entity types must be one of: Policy, Regulation, Application, Cloud Service, Storage, Data Asset, Compliance Rule, Risk, Department, Employee, Audit, Document
4. Relationship types must be one of: STORES, USES, BELONGS_TO, VIOLATES, GOVERNS, REFERENCES, OWNS, CONNECTED_TO, DEPENDS_ON
5. Confidence scores: 0.0 to 1.0
6. Keep "description" under 80 characters.
7. Extract at most 8 entities and 8 relationships per chunk.

OUTPUT FORMAT (return exactly this structure, nothing else):
{"entities":[{"name":"string","type":"string","description":"string","confidence":0.9}],"relationships":[{"source_entity":"string","relationship_type":"string","target_entity":"string","confidence":0.9,"evidence":"string"}]}"""

    @staticmethod
    def build_extraction_prompt(chunk_text: str, source_doc: str) -> str:
        # Truncate chunk to max 1500 chars to avoid token overflow
        truncated = chunk_text[:1500] if len(chunk_text) > 1500 else chunk_text
        return f"""Extract compliance entities and relationships from this chunk of '{source_doc}'.

CHUNK:
{truncated}

Return ONLY the JSON object. No other text."""
