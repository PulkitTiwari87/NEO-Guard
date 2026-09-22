import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiRequestError } from '../services/api/client';

// Mock global fetch
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

// Mock import.meta.env
vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000');

describe('ApiRequestError', () => {
  it('carries status and message', () => {
    const err = new ApiRequestError(404, 'NEO not found', 'NEO not found');
    expect(err.status).toBe(404);
    expect(err.message).toBe('NEO not found');
    expect(err.name).toBe('ApiRequestError');
  });
});

// Integration-style test of the client behavior
describe('apiFetch error handling', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('throws ApiRequestError on 404 with detail string', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'NEO not found' }),
    });

    const { apiFetch } = await import('../services/api/client');
    let err: unknown;
    try {
      await apiFetch('/api/neos/999');
    } catch (e) {
      err = e;
    }
    expect(err).toBeInstanceOf(ApiRequestError);
    expect((err as ApiRequestError).status).toBe(404);
    expect((err as ApiRequestError).message).toBe('NEO not found');
  });

  it('throws with generic message on 500', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ detail: 'Internal server error' }),
    });

    const { apiFetch } = await import('../services/api/client');
    await expect(apiFetch('/api/neos')).rejects.toMatchObject({
      status: 500,
    });
  });
});
