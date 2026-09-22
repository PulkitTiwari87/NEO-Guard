import { apiFetch, buildQuery } from './client';
import type { NeoList, NeoDetail, ApproachList, NeoListParams } from '../../types/api';

export async function fetchNeos(params: NeoListParams = {}): Promise<NeoList> {
  const qs = buildQuery({
    page: params.page,
    per_page: params.per_page,
    is_hazardous: params.is_hazardous,
    search: params.search,
    sort: params.sort,
  });
  return apiFetch<NeoList>(`/api/neos${qs}`);
}

export async function fetchNeo(id: number): Promise<NeoDetail> {
  return apiFetch<NeoDetail>(`/api/neos/${id}`);
}

export async function fetchApproaches(neoId: number): Promise<ApproachList> {
  return apiFetch<ApproachList>(`/api/neos/${neoId}/approaches`);
}
