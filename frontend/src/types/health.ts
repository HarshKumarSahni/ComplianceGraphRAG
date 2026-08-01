// Health Status Types

export interface ServiceHealth {
  status: 'healthy' | 'unhealthy' | 'mock_mode' | 'configured' | 'unconfigured' | 'connected' | 'disconnected';
  details?: Record<string, any>;
}

export interface HealthStatus {
  status: 'online' | 'degraded' | 'offline';
  environment: string;
  project_name: string;
  version: string;
  services: {
    neo4j: string;
    openrouter: string;
    cloudinary: string;
  };
}
