import { useEffect, useState } from 'react';

export interface AsyncState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

/** Run an async function on dependency change, tracking loading/error state. */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ data: null, error: null, loading: true });

  useEffect(() => {
    let alive = true;
    setState({ data: null, error: null, loading: true });
    fn()
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch(
        (e: unknown) =>
          alive &&
          setState({
            data: null,
            error: e instanceof Error ? e.message : String(e),
            loading: false,
          }),
      );
    return () => {
      alive = false;
    };
  }, deps);

  return state;
}
