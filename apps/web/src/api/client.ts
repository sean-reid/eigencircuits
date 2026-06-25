import type { GenerateResponse } from '../types/paperModel';

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api';

export async function generatePaper(seed?: string): Promise<GenerateResponse> {
  const query = seed ? `?seed=${encodeURIComponent(seed)}` : '';
  const res = await fetch(`${BASE}/generate${query}`);
  if (!res.ok) throw new Error(`generate failed (${res.status})`);
  return (await res.json()) as GenerateResponse;
}
