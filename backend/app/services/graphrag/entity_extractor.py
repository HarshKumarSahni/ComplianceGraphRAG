import re
from typing import List, Dict, Any
from app.core.logger import logger
from app.services.openrouter_client import OpenRouterClient as ExtractionOpenRouterClient


# Common English stop words for heuristic extraction
_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "about", "up",
    "what", "which", "who", "whom", "this", "that", "these", "those", "am",
    "it", "its", "my", "your", "his", "her", "our", "their", "me", "him",
    "us", "them", "i", "you", "he", "she", "we", "they",
})


class EntityExtractor:
    """Extracts key entities and keywords from a natural language question.

    Two strategies:
    1. LLM-based: sends to OpenRouter for structured entity extraction
    2. Heuristic fallback: tokenization + stop word removal + capitalized phrase detection
    """

    def __init__(self, openrouter_client: ExtractionOpenRouterClient):
        self.openrouter = openrouter_client

    async def extract(self, question: str) -> Dict[str, Any]:
        """Extract entities and keywords from the question.

        Returns:
            {
                "entities": ["GDPR", "Article 32", ...],
                "keywords": ["compliance", "data protection", ...]
            }
        """
        # Try LLM-based extraction first
        if self.openrouter.api_key:
            try:
                return await self._extract_with_llm(question)
            except Exception as e:
                logger.warning(f"LLM entity extraction failed, using heuristic: {e}")

        # Fallback to heuristic
        return self._extract_heuristic(question)

    async def _extract_with_llm(self, question: str) -> Dict[str, Any]:
        """Use OpenRouter to extract entities from the question."""
        system_prompt = """You are an entity extraction engine for compliance questions.
Given a user question, extract:
1. Named entities (regulations, policies, organizations, systems, people, standards)
2. Key search keywords

Return valid JSON:
{
  "entities": ["Entity1", "Entity2"],
  "keywords": ["keyword1", "keyword2"]
}

Rules:
- Extract ONLY entities and keywords that appear in the question
- Keep entity names as they appear in the question
- Keywords should be single important words or short phrases
- Do NOT add entities that are not in the question"""

        result = await self.openrouter.generate_json(
            prompt=f"Extract entities and keywords from this compliance question:\n\n\"{question}\"",
            system_prompt=system_prompt,
        )

        entities = result.get("entities", [])
        keywords = result.get("keywords", [])

        # Ensure we always have at least heuristic keywords as backup
        if not entities and not keywords:
            return self._extract_heuristic(question)

        return {"entities": entities, "keywords": keywords}

    def _extract_heuristic(self, question: str) -> Dict[str, Any]:
        """Heuristic entity/keyword extraction using simple NLP rules."""
        # Extract capitalized phrases (likely proper nouns / entity names)
        capitalized = re.findall(r'\b[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)*\b', question)
        entities = [phrase for phrase in capitalized if len(phrase) > 1]

        # Tokenize and remove stop words for keywords
        tokens = re.findall(r'\b[a-zA-Z]{2,}\b', question.lower())
        keywords = [t for t in tokens if t not in _STOP_WORDS and len(t) > 2]

        # Deduplicate while preserving order
        seen_entities = set()
        unique_entities = []
        for e in entities:
            if e.lower() not in seen_entities:
                seen_entities.add(e.lower())
                unique_entities.append(e)

        seen_kw = set()
        unique_keywords = []
        for k in keywords:
            if k not in seen_kw:
                seen_kw.add(k)
                unique_keywords.append(k)

        return {"entities": unique_entities, "keywords": unique_keywords}
