// Minimal API client for the Sadot backend.

// Browser calls use the public URL (inlined at build time via NEXT_PUBLIC_*).
const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// On the server (SSR) prefer an internal URL (e.g. http://backend:8000) so we
// don't hairpin out through the public domain. Falls back to the public URL.
export const API_URL =
  typeof window === "undefined"
    ? process.env.INTERNAL_API_URL || PUBLIC_API_URL
    : PUBLIC_API_URL;

export type DogPublic = {
  id: number;
  name: string | null;
  breed: string | null;
  age: number | null;
  gender: string;
  size: string | null;
  color: string | null;
  good_with_children: boolean | null;
  good_with_dogs: boolean | null;
  good_with_cats: boolean | null;
  suitable_for_apartment: boolean | null;
  suitable_for_first_time_owner: boolean | null;
  public_description: string | null;
  public_area: string | null;
  current_location_type: string;
  status: string;
  photos: string[];
};

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

// ---- Public ----
export async function getPublicDogs(): Promise<DogPublic[]> {
  return handle(await fetch(`${API_URL}/api/v1/public/dogs`, { cache: "no-store" }));
}

export async function getPublicDog(id: number): Promise<DogPublic> {
  return handle(await fetch(`${API_URL}/api/v1/public/dogs/${id}`, { cache: "no-store" }));
}

export async function submitSurrenderLead(payload: Record<string, unknown>) {
  return handle(
    await fetch(`${API_URL}/api/v1/public/leads/surrender`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function submitAdoptionLead(payload: Record<string, unknown>) {
  return handle(
    await fetch(`${API_URL}/api/v1/public/leads/adoption`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

// ---- Auth / admin ----
export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const data = await handle<{ access_token: string }>(res);
  return data.access_token;
}

export async function authGet<T>(path: string, token: string): Promise<T> {
  return handle(
    await fetch(`${API_URL}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })
  );
}
