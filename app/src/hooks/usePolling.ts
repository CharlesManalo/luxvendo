import { useState, useEffect, useCallback, useRef } from 'react';

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number = 10000,
  enabled: boolean = true
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval>>(undefined);

  const fetchData = useCallback(async () => {
    try {
      const result = await fetcher();
      setData(result);
      setError(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Polling error';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [fetcher]);

  useEffect(() => {
    if (!enabled) {
      setIsLoading(false);
      return;
    }

    fetchData();
    intervalRef.current = setInterval(fetchData, intervalMs);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, intervalMs, enabled]);

  return { data, isLoading, error, refresh: fetchData };
}
