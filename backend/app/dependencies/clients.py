from typing import Optional, List, Dict, Any
from app.core.config import Settings
from app.core.logger import logger

class Neo4jClient:
    """Production Neo4j driver wrapper with connection pooling and health checks."""

    def __init__(self, settings: Settings):
        self.uri = settings.NEO4J_URI
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
        self._driver = None

    def connect(self):
        """Initialize the Neo4j driver and verify connectivity."""
        if not self.uri:
            logger.warning("NEO4J_URI is empty. Neo4j client running in mock mode.")
            return

        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_pool_size=50,
                connection_acquisition_timeout=30,
            )
            self._driver.verify_connectivity()
            logger.info(f"Neo4j driver connected to {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._driver = None

    def close(self):
        """Gracefully close the Neo4j driver."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j driver connection closed.")

    def check_health(self) -> str:
        """Return connectivity status."""
        if not self._driver:
            return "disconnected"
        try:
            self._driver.verify_connectivity()
            return "connected"
        except Exception:
            return "unhealthy"

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a write/general Cypher query and return records as dicts."""
        if not self._driver:
            logger.warning("Neo4j driver not initialized. Returning empty result.")
            return []

        with self._driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_read(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a read-only Cypher query using an explicit read transaction."""
        if not self._driver:
            logger.warning("Neo4j driver not initialized. Returning empty result.")
            return []

        def _read_tx(tx):
            result = tx.run(query, parameters or {})
            return [record.data() for record in result]

        with self._driver.session(database=self.database) as session:
            return session.execute_read(_read_tx)

class CloudinaryClient:
    def __init__(self, settings: Settings):
        self.cloud_name = settings.CLOUDINARY_CLOUD_NAME
        self.api_key = settings.CLOUDINARY_API_KEY
        self.api_secret = settings.CLOUDINARY_API_SECRET

    def initialize(self):
        logger.info(f"Initialized Cloudinary Client wrapper for cloud: {self.cloud_name}")

    def check_health(self) -> str:
        if not (self.cloud_name and self.api_key and self.api_secret):
            return "unconfigured (mock_mode)"
        return "configured"

class OpenRouterClient:
    def __init__(self, settings: Settings):
        self.api_key = settings.OPENROUTER_API_KEY
        self.primary_model = getattr(settings, 'OPENROUTER_PRIMARY_MODEL', None)

    def initialize(self):
        logger.info(f"Initialized OpenRouter Client wrapper for model: {self.primary_model}")

