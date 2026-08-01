import { useQuery } from '@tanstack/react-query';
import { healthService } from '@/services/health.service';

export function useHealth() {
  return useQuery({
    queryKey: ['health-status'],
    queryFn: () => healthService.getHealthStatus(),
    refetchInterval: 30000, // Poll backend every 30 seconds
    retry: 2,
  });
}
