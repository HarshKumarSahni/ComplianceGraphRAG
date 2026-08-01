from typing import List, Dict, Any


class QueryPromptBuilder:
    """Constructs system and user prompts for GraphRAG answer generation.

    The prompt enforces grounded answering: the LLM must only use the
    provided graph facts and document chunks. If the evidence does not
    support an answer, the LLM must explicitly say so.
    """

    @staticmethod
    def get_system_prompt() -> str:
        return """You are GraphGuard AI, an enterprise compliance analysis assistant.

RULES — follow these strictly:
1. Answer ONLY using the provided GRAPH FACTS and DOCUMENT CHUNKS below.
2. If the evidence does not contain enough information to answer, reply:
   "The available evidence does not contain sufficient information to answer this question."
3. Cite the specific chunks you used by their chunk_id.
4. Be precise, professional, and concise.
5. Do NOT hallucinate or use external knowledge.
6. Provide a confidence score (0.0–1.0) reflecting how well the evidence supports your answer.

OUTPUT FORMAT — return valid JSON:
{
  "answer": "Your grounded answer here.",
  "confidence": 0.85,
  "cited_chunks": ["chunk-001", "chunk-002"]
}"""

    @staticmethod
    def build_user_prompt(
        question: str,
        graph_facts: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
    ) -> str:
        """Assemble the user prompt with question, graph context, and chunk context."""
        sections = [f"QUESTION:\n{question}"]

        # -- Graph Facts Section --
        if graph_facts:
            facts_text = QueryPromptBuilder._format_graph_facts(graph_facts)
            sections.append(f"GRAPH FACTS:\n{facts_text}")
        else:
            sections.append("GRAPH FACTS:\nNo relevant graph facts were retrieved.")

        # -- Document Chunks Section --
        if chunks:
            chunks_text = QueryPromptBuilder._format_chunks(chunks)
            sections.append(f"DOCUMENT CHUNKS:\n{chunks_text}")
        else:
            sections.append("DOCUMENT CHUNKS:\nNo relevant document chunks were retrieved.")

        sections.append("Based on the above evidence, answer the question in the specified JSON format.")

        return "\n\n".join(sections)

    @staticmethod
    def _format_graph_facts(graph_data: List[Dict[str, Any]]) -> str:
        """Format graph nodes and edges into readable triples."""
        lines = []
        for item in graph_data:
            if "source" in item and "target" in item:
                # This is an edge / relationship
                rel_type = item.get("type", "RELATED_TO")
                confidence = item.get("confidence", "")
                conf_str = f" (confidence: {confidence})" if confidence else ""
                lines.append(f"- {item['source']} --[{rel_type}]--> {item['target']}{conf_str}")
            elif "name" in item:
                # This is a node / entity
                entity_type = item.get("type", "Entity")
                desc = item.get("description", "")
                desc_str = f": {desc}" if desc else ""
                lines.append(f"- [{entity_type}] {item['name']}{desc_str}")

        return "\n".join(lines) if lines else "No graph facts available."

    @staticmethod
    def _format_chunks(chunks: List[Dict[str, Any]]) -> str:
        """Format document chunks with their IDs and source metadata."""
        lines = []
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "unknown")
            doc_name = chunk.get("document_name", "unknown")
            text = chunk.get("text", "")
            page = chunk.get("page_number")
            page_str = f" | Page {page}" if page else ""

            lines.append(f"[{chunk_id}] (Source: {doc_name}{page_str})")
            lines.append(text.strip())
            lines.append("")  # blank line separator

        return "\n".join(lines) if lines else "No chunks available."
