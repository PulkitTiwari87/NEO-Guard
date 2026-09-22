import { apiFetch, buildQuery } from './client';
import type { PredictRequest, PredictResponse } from '../../types/api';

export async function predict(
  request: PredictRequest,
  explain: boolean = true,
): Promise<PredictResponse> {
  const qs = buildQuery({ explain });
  return apiFetch<PredictResponse>(`/api/predict${qs}`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
