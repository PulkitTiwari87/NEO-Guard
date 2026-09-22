import { apiFetch } from './client';
import type { Analytics } from '../../types/api';

export async function fetchAnalytics(): Promise<Analytics> {
  return apiFetch<Analytics>('/api/analytics');
}
