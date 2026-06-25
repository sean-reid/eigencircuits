import type { AbsResponse, ArchiveResponse, ListResponse, SearchResponse } from '../types/api';

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api';

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`request failed (${res.status})`);
  return (await res.json()) as T;
}

export function fetchArchive(): Promise<ArchiveResponse> {
  return getJSON<ArchiveResponse>('/archive');
}

export function fetchList(
  cat: string,
  period: string,
  skip: number,
  show: number,
): Promise<ListResponse> {
  const q = new URLSearchParams({ cat, period, skip: String(skip), show: String(show) });
  return getJSON<ListResponse>(`/list?${q.toString()}`);
}

export function fetchAbs(id: string): Promise<AbsResponse> {
  return getJSON<AbsResponse>(`/abs?id=${encodeURIComponent(id)}`);
}

export function fetchSearch(
  query: string,
  cat: string,
  skip: number,
  show: number,
): Promise<SearchResponse> {
  const q = new URLSearchParams({ q: query, cat, skip: String(skip), show: String(show) });
  return getJSON<SearchResponse>(`/search?${q.toString()}`);
}
