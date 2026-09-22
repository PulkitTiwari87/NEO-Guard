import { apiFetch } from './client';
import type { ModelList, ModelDetail } from '../../types/api';

export async function fetchModels(): Promise<ModelList> {
  return apiFetch<ModelList>('/api/models');
}

export async function fetchModel(version: string): Promise<ModelDetail> {
  return apiFetch<ModelDetail>(`/api/models/${encodeURIComponent(version)}`);
}
