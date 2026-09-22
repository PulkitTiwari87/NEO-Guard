import { BASE_URL } from './client';
import type { Health } from '../../types/api';

/**
 * Health endpoint — returns 200 or 503; we always want the body.
 * Does not throw on 503 so the UI can display the degraded banner.
 */
export async function fetchHealth(): Promise<Health> {
  const res = await fetch(`${BASE_URL}/api/health`);
  // Always parse the body — both 200 and 503 return the same shape
  return res.json() as Promise<Health>;
}
