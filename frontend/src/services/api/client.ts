/**
 * Base API client with consistent error handling.
 * All API modules go through this — never use raw fetch() in components.
 */

import type { ApiError } from '../../types/api';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

export class ApiRequestError extends Error {
  readonly status: number;
  readonly detail: ApiError['detail'];

  constructor(status: number, message: string, detail?: ApiError['detail']) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.detail = detail;
  }
}

async function parseError(res: Response): Promise<ApiRequestError> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    body = null;
  }

  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: ApiError['detail'] }).detail;
    if (typeof detail === 'string') {
      return new ApiRequestError(res.status, detail, detail);
    }
    if (Array.isArray(detail)) {
      const msg = detail.map(d => d.msg).join('; ');
      return new ApiRequestError(res.status, msg, detail);
    }
  }

  // 5xx — do not expose detail
  if (res.status >= 500) {
    return new ApiRequestError(res.status, 'A server error occurred. Please try again.');
  }
  return new ApiRequestError(res.status, res.statusText || 'Request failed');
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
    ...options,
  });

  if (!res.ok) {
    throw await parseError(res);
  }

  // health returns 503 but we still want the body — handled in healthApi separately
  return res.json() as Promise<T>;
}

/** Build a query string from an object, omitting undefined/null values. */
export function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') {
      qs.set(k, String(v));
    }
  }
  const s = qs.toString();
  return s ? `?${s}` : '';
}

export { BASE_URL };
