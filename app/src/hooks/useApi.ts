import { useState, useCallback } from 'react';

interface UseApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
}

export function useApi() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(async <T,>(url: string, options: UseApiOptions = {}): Promise<T | null> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const res = await fetch(url, {
        method: options.method || 'GET',
        headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
        body: options.body ? JSON.stringify(options.body) : undefined,
        credentials: 'include',
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || data.message || `Error ${res.status}`);
      }

      // Handle empty responses
      const contentType = res.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        return await res.json() as T;
      }
      return null as T;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(msg);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { request, isLoading, error, setError };
}

// Direct API helpers (non-hook)
export async function apiGet<T>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: 'include' });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Error ${res.status}`);
  }
  return res.json();
}

export async function apiPost<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'include',
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Error ${res.status}`);
  }
  return res.json();
}

export async function apiDelete(url: string): Promise<void> {
  const res = await fetch(url, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Error ${res.status}`);
  }
}
