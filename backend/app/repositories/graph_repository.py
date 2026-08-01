from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IGraphRepository(ABC):
    @abstractmethod
    async def upsert_nodes_and_edges(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
        pass

    @abstractmethod
    async def get_graph(self) -> Dict[str, Any]:
        pass

class GraphRepository(IGraphRepository):
    def __init__(self, neo4j_client):
        self.client = neo4j_client

    async def upsert_nodes_and_edges(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
        return True

    async def get_graph(self) -> Dict[str, Any]:
        return {"nodes": [], "edges": []}
