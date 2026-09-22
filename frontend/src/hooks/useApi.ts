import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '../services/api/healthApi';
import { fetchAnalytics } from '../services/api/analyticsApi';
import { fetchNeos, fetchNeo, fetchApproaches } from '../services/api/neoApi';
import { fetchModels, fetchModel } from '../services/api/modelApi';
import type { NeoListParams } from '../types/api';

export const queryKeys = {
  health: ['health'] as const,
  analytics: ['analytics'] as const,
  neos: (params: NeoListParams) => ['neos', params] as const,
  neo: (id: number) => ['neo', id] as const,
  approaches: (id: number) => ['approaches', id] as const,
  models: ['models'] as const,
  model: (version: string) => ['model', version] as const,
};

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: fetchHealth,
    refetchInterval: 60_000, // re-check every minute
    staleTime: 30_000,
  });
}

export function useAnalytics() {
  return useQuery({
    queryKey: queryKeys.analytics,
    queryFn: fetchAnalytics,
    staleTime: 5 * 60_000,
  });
}

export function useNeos(params: NeoListParams) {
  return useQuery({
    queryKey: queryKeys.neos(params),
    queryFn: () => fetchNeos(params),
    staleTime: 60_000,
    placeholderData: (prev) => prev,
  });
}

export function useNeo(id: number) {
  return useQuery({
    queryKey: queryKeys.neo(id),
    queryFn: () => fetchNeo(id),
    staleTime: 5 * 60_000,
    enabled: !!id,
  });
}

export function useApproaches(neoId: number) {
  return useQuery({
    queryKey: queryKeys.approaches(neoId),
    queryFn: () => fetchApproaches(neoId),
    staleTime: 5 * 60_000,
    enabled: !!neoId,
  });
}

export function useModels() {
  return useQuery({
    queryKey: queryKeys.models,
    queryFn: fetchModels,
    staleTime: 5 * 60_000,
  });
}

export function useModel(version: string) {
  return useQuery({
    queryKey: queryKeys.model(version),
    queryFn: () => fetchModel(version),
    staleTime: 5 * 60_000,
    enabled: !!version,
  });
}
