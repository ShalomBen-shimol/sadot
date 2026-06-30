// API client for the Sadot backend.
//
// Mirrors the FastAPI routes under backend/app/api/v1. Admin endpoints require a
// Bearer JWT (see authGet/authPost/authPatch/authUpload). Public endpoints are
// unauthenticated. Keep types in sync with the backend models/schemas.

// Browser calls use the public URL (inlined at build time via NEXT_PUBLIC_*).
const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// On the server (SSR) prefer an internal URL (e.g. http://backend:8000) so we
// don't hairpin out through the public domain. Falls back to the public URL.
export const API_URL =
  typeof window === "undefined"
    ? process.env.INTERNAL_API_URL || PUBLIC_API_URL
    : PUBLIC_API_URL;

// ============================================================================
// Enums (string unions mirroring app/models/enums.py)
// ============================================================================
export type UserRole = "admin" | "field_worker" | "viewer";

export type DogStatus =
  | "draft"
  | "pending_surrender"
  | "in_facility"
  | "available_for_adoption"
  | "reserved"
  | "adopted"
  | "inactive";

export type DogGender = "male" | "female" | "unknown";

export type DogSize = "small" | "medium" | "large" | "xlarge";

export type LocationType = "home" | "facility" | "adopted";

export type SurrenderType = "facility" | "full" | "home_subscription";

export type SurrenderStatus =
  | "new_lead"
  | "contacted"
  | "waiting_for_details"
  | "waiting_for_payment"
  | "active_home_subscription"
  | "waiting_for_documents"
  | "ownership_transfer_in_progress"
  | "transferred_to_facility"
  | "available_for_adoption"
  | "cancelled"
  | "completed";

export type PaymentStatus = "pending" | "paid" | "failed" | "refunded";

export type AdoptionStatus =
  | "new_lead"
  | "screening"
  | "waiting_for_call"
  | "meeting_scheduled"
  | "waiting_for_decision"
  | "approved"
  | "waiting_for_signatures"
  | "waiting_for_documents"
  | "authority_submission_ready"
  | "sent_to_authority"
  | "waiting_for_authority_confirmation"
  | "ownership_transferred"
  | "completed"
  | "rejected"
  | "cancelled";

export type AdoptionLeadStatus =
  | "new"
  | "contacted"
  | "matched"
  | "converted"
  | "closed";

export type TransferType =
  | "surrender_to_facility"
  | "facility_to_adopter"
  | "direct_surrenderer_to_adopter";

export type OwnershipTransferStatus =
  | "draft"
  | "waiting_for_documents"
  | "waiting_for_signatures"
  | "ready_to_send"
  | "sent_to_authority"
  | "followup_required"
  | "confirmed"
  | "failed"
  | "stopped_manually";

export type DocumentType =
  | "ownership_transfer_form"
  | "receiver_approval_form"
  | "id_card_surrenderer"
  | "id_card_receiver"
  | "adopter_with_dog_photo"
  | "authority_submission"
  | "authority_confirmation"
  | "other";

export type DocumentStatus = "pending" | "uploaded" | "approved" | "rejected";

export type SignatureType = "surrenderer" | "receiver" | "adopter";

export type SignatureStatus =
  | "pending"
  | "sent"
  | "signed"
  | "declined"
  | "expired";

export type TaskStatus = "open" | "in_progress" | "done" | "cancelled";

export type TaskPriority = "low" | "normal" | "high" | "urgent";

export type MessageChannel = "whatsapp" | "email" | "sms" | "system";

export type MessageDirection = "inbound" | "outbound";

export type MessageStatus = "queued" | "sent" | "delivered" | "read" | "failed";

export type EntityType =
  | "dog"
  | "person"
  | "surrender_case"
  | "adoption_case"
  | "adoption_lead"
  | "ownership_transfer";

// ============================================================================
// Entity types (mirroring app/models/*)
// ============================================================================
export type User = {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  role: UserRole;
  is_active: boolean;
};

export type DogPublic = {
  id: number;
  name: string | null;
  breed: string | null;
  age: number | null;
  gender: DogGender;
  size: DogSize | null;
  color: string | null;
  good_with_children: boolean | null;
  good_with_dogs: boolean | null;
  good_with_cats: boolean | null;
  suitable_for_apartment: boolean | null;
  suitable_for_first_time_owner: boolean | null;
  public_description: string | null;
  public_area: string | null;
  current_location_type: LocationType;
  status: DogStatus;
  photos: string[];
};

export type Dog = {
  id: number;
  name: string | null;
  breed: string | null;
  age: number | null;
  gender: DogGender;
  size: DogSize | null;
  color: string | null;
  chip_number: string | null;
  is_neutered: boolean | null;
  is_vaccinated: boolean | null;
  medical_notes: string | null;
  behavior_notes: string | null;
  good_with_children: boolean | null;
  good_with_dogs: boolean | null;
  good_with_cats: boolean | null;
  suitable_for_apartment: boolean | null;
  suitable_for_first_time_owner: boolean | null;
  status: DogStatus;
  current_location_type: LocationType;
  current_owner_person_id: number | null;
  public_description: string | null;
  internal_notes: string | null;
  public_area: string | null;
  created_at: string;
};

export type DogPhoto = {
  id: number;
  dog_id: number;
  file_url: string;
  is_primary: boolean;
  created_at: string;
};

export type Person = {
  id: number;
  first_name: string;
  last_name: string | null;
  phone: string | null;
  email: string | null;
  city: string | null;
  address_private: string | null;
  id_number_encrypted: string | null;
  notes: string | null;
  created_at: string;
};

export type SurrenderCase = {
  id: number;
  dog_id: number | null;
  surrenderer_person_id: number;
  surrender_type: SurrenderType;
  monthly_price: number | null;
  total_required_amount: number | null;
  accumulated_credit: number;
  start_date: string | null;
  status: SurrenderStatus;
  reason: string | null;
  privacy_required: boolean;
  allow_direct_contact: boolean;
  created_at: string;
};

export type SubscriptionPayment = {
  id: number;
  surrender_case_id: number;
  amount: number;
  month_index: number;
  payment_date: string | null;
  status: PaymentStatus;
  payment_provider_reference: string | null;
  created_at: string;
};

export type AdoptionLead = {
  id: number;
  person_id: number;
  dog_id: number | null;
  preferred_size: DogSize | null;
  preferred_breed: string | null;
  has_children: boolean | null;
  has_other_dogs: boolean | null;
  home_type: string | null;
  experience_level: string | null;
  hours_alone: string | null;
  consent_messages: boolean;
  consent_privacy: boolean;
  status: AdoptionLeadStatus;
  source: string | null;
  notes: string | null;
  created_at: string;
};

export type AdoptionCase = {
  id: number;
  dog_id: number;
  adopter_person_id: number;
  surrender_case_id: number | null;
  adoption_lead_id: number | null;
  status: AdoptionStatus;
  meeting_date: string | null;
  is_direct_home_adoption: boolean;
  created_at: string;
};

export type OwnershipTransfer = {
  id: number;
  dog_id: number;
  from_person_id: number | null;
  to_person_id: number | null;
  from_authority_id: number | null;
  to_authority_id: number | null;
  transfer_type: TransferType;
  status: OwnershipTransferStatus;
  sent_to_authority_at: string | null;
  confirmed_at: string | null;
  last_followup_at: string | null;
  next_followup_at: string | null;
  notes: string | null;
  created_at: string;
};

export type Municipality = {
  id: number;
  city_name: string;
  authority_name: string | null;
  district: string | null;
  vet_department_name: string | null;
  vet_name: string | null;
  license_number: string | null;
  email: string | null;
  phone: string | null;
  website: string | null;
  notes: string | null;
  is_active: boolean;
};

export type Locality = {
  id: number;
  name: string;
  name_normalized: string;
  symbol: string | null;
  subdistrict: string | null;
  district: string | null;
  municipality_id: number | null;
  needs_review: boolean;
};

export type LocalityListResponse = {
  total: number;
  items: Locality[];
};

export type LocalityResolveResponse = {
  query: string;
  locality: Locality | null;
  authority: Municipality | null;
  resolved: boolean;
};

export type DocumentRecord = {
  id: number;
  related_entity_type: EntityType;
  related_entity_id: number;
  document_type: DocumentType;
  file_url: string | null;
  uploaded_by_user_id: number | null;
  uploaded_by_person_id: number | null;
  status: DocumentStatus;
  is_sensitive: boolean;
  created_at: string;
};

export type SignatureRequest = {
  id: number;
  related_entity_type: EntityType;
  related_entity_id: number;
  signer_person_id: number;
  signature_type: SignatureType;
  status: SignatureStatus;
  sign_url: string | null;
  signed_at: string | null;
  provider_reference: string | null;
  created_at: string;
};

export type Task = {
  id: number;
  title: string;
  description: string | null;
  related_entity_type: EntityType | null;
  related_entity_id: number | null;
  assigned_to_user_id: number | null;
  due_date: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  is_followup: boolean;
  created_at: string;
};

export type Message = {
  id: number;
  person_id: number | null;
  channel: MessageChannel;
  direction: MessageDirection;
  content: string;
  status: MessageStatus;
  provider_reference: string | null;
  intent: string | null;
  created_at: string;
};

// ---- Aggregate response shapes (backoffice case files) ----
export type DashboardSummary = {
  dogs_total: number;
  dogs_available: number;
  dogs_in_facility: number;
  dogs_adopted: number;
  surrender_cases: number;
  adoption_leads: number;
  adoption_cases: number;
  open_tasks: number;
  transfers_awaiting_authority: number;
};

export type PersonFile = {
  person: Person;
  dogs_owned: Dog[];
  surrender_cases: SurrenderCase[];
  adoption_cases: AdoptionCase[];
  adoption_leads: AdoptionLead[];
  documents: DocumentRecord[];
  recent_messages: Message[];
};

export type DogFile = {
  dog: Dog;
  current_owner: Person | null;
  surrender_cases: SurrenderCase[];
  adoption_cases: AdoptionCase[];
  adoption_leads: AdoptionLead[];
  ownership_transfers: OwnershipTransfer[];
  documents: DocumentRecord[];
  photos: DogPhoto[];
};

export type OwnershipTransferDetail = {
  transfer: OwnershipTransfer;
  dog: Dog | null;
  from_person: Person | null;
  to_person: Person | null;
  from_authority_name: string | null;
  to_authority_name: string | null;
  documents: DocumentRecord[];
  signature_requests: SignatureRequest[];
  required_documents: string[];
  documents_complete: boolean;
};

// ---- Action / misc response shapes ----
export type LeadResponse = {
  detail: string;
  person_id: number;
  case_id: number | null;
  lead_id: number | null;
};

export type RequiredDocumentsResponse = {
  required: DocumentType[];
  complete: boolean;
};

export type StartFacilityTransferResponse = {
  detail: string;
  ownership_transfer_id: number;
};

export type ConvertToFacilityResponse = {
  detail: string;
  accumulated_credit: number;
  ownership_transfer_id: number;
};

export type RunFollowupsResponse = {
  detail: string;
  reminders_created: number;
};

export type QrLinks = {
  surrender: string;
  adopt: string;
};

export type StatusTransition = {
  status: string;
  note?: string | null;
};

// ============================================================================
// Low-level helpers
// ============================================================================
async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

// Token key + login path must match _components/ui.tsx and next.config.js basePath.
const TOKEN_KEY = "sadot_token";
const LOGIN_PATH = "/crm/admin/login";

// When an authenticated request is rejected (expired/invalid token, or the user
// no longer exists), drop the dead token and bounce to login. Without this the
// admin pages just render the raw "Could not validate credentials" 401 with no
// way back in. No-op during SSR and when already on the login screen.
function handleUnauthorized(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* localStorage unavailable */
  }
  if (!window.location.pathname.endsWith("/admin/login")) {
    window.location.href = LOGIN_PATH;
  }
}

// Like handle(), but auto-recovers from 401 by clearing the token + redirecting.
async function handleAuthed<T>(res: Response): Promise<T> {
  if (res.status === 401) handleUnauthorized();
  return handle<T>(res);
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

export async function authGet<T>(path: string, token: string): Promise<T> {
  return handleAuthed(
    await fetch(`${API_URL}${path}`, {
      headers: authHeaders(token),
      cache: "no-store",
    })
  );
}

export async function authPost<T>(
  path: string,
  token: string,
  body?: unknown
): Promise<T> {
  return handleAuthed(
    await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: {
        ...authHeaders(token),
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
    })
  );
}

export async function authPatch<T>(
  path: string,
  token: string,
  body: unknown
): Promise<T> {
  return handleAuthed(
    await fetch(`${API_URL}${path}`, {
      method: "PATCH",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    })
  );
}

export async function authPut<T>(
  path: string,
  token: string,
  body: unknown
): Promise<T> {
  return handleAuthed(
    await fetch(`${API_URL}${path}`, {
      method: "PUT",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    })
  );
}

export async function authDelete(path: string, token: string): Promise<void> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "DELETE",
    headers: authHeaders(token),
    cache: "no-store",
  });
  if (res.status === 401) handleUnauthorized();
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
}

// Multipart upload with a Bearer token. Do NOT set Content-Type manually —
// the browser must add the multipart boundary itself.
export async function authUpload<T>(
  path: string,
  token: string,
  form: FormData
): Promise<T> {
  return handleAuthed(
    await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: authHeaders(token),
      body: form,
      cache: "no-store",
    })
  );
}

// Unauthenticated multipart/url-encoded POST helper (public forms).
export async function postForm<T>(
  path: string,
  form: FormData
): Promise<T> {
  return handle(
    await fetch(`${API_URL}${path}`, {
      method: "POST",
      body: form,
    })
  );
}

// Build a query string from a partial record, skipping null/undefined values.
function qs(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined) {
      search.set(key, String(value));
    }
  }
  const str = search.toString();
  return str ? `?${str}` : "";
}

// ============================================================================
// Public (unauthenticated)
// ============================================================================
export async function getPublicDogs(): Promise<DogPublic[]> {
  return handle(await fetch(`${API_URL}/api/v1/public/dogs`, { cache: "no-store" }));
}

export async function getPublicDog(id: number): Promise<DogPublic> {
  return handle(await fetch(`${API_URL}/api/v1/public/dogs/${id}`, { cache: "no-store" }));
}

export async function submitSurrenderLead(
  payload: Record<string, unknown>
): Promise<LeadResponse> {
  return handle(
    await fetch(`${API_URL}/api/v1/public/leads/surrender`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function submitAdoptionLead(
  payload: Record<string, unknown>
): Promise<LeadResponse> {
  return handle(
    await fetch(`${API_URL}/api/v1/public/leads/adoption`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

// ============================================================================
// Auth
// ============================================================================
export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const data = await handle<{ access_token: string; token_type: string }>(res);
  return data.access_token;
}

export async function getMe(token: string): Promise<User> {
  return authGet<User>("/api/v1/auth/me", token);
}

// ============================================================================
// Dashboard
// ============================================================================
export async function getDashboardSummary(token: string): Promise<DashboardSummary> {
  return authGet<DashboardSummary>("/api/v1/dashboard/summary", token);
}

// ============================================================================
// Dogs
// ============================================================================
export async function listDogs(
  token: string,
  params: { status?: DogStatus; offset?: number; limit?: number } = {}
): Promise<Dog[]> {
  return authGet<Dog[]>(`/api/v1/dogs${qs(params)}`, token);
}

export async function getDog(token: string, dogId: number): Promise<Dog> {
  return authGet<Dog>(`/api/v1/dogs/${dogId}`, token);
}

export async function getDogFile(token: string, dogId: number): Promise<DogFile> {
  return authGet<DogFile>(`/api/v1/dogs/${dogId}/file`, token);
}

// Editable basics for a dog (PATCH /dogs/{id}). All fields optional.
export type DogUpdate = {
  name?: string | null;
  breed?: string | null;
  age?: number | null;
  gender?: DogGender | null;
  size?: DogSize | null;
  color?: string | null;
  chip_number?: string | null;
  is_neutered?: boolean | null;
  is_vaccinated?: boolean | null;
  medical_notes?: string | null;
  behavior_notes?: string | null;
  good_with_children?: boolean | null;
  good_with_dogs?: boolean | null;
  good_with_cats?: boolean | null;
  suitable_for_apartment?: boolean | null;
  suitable_for_first_time_owner?: boolean | null;
  status?: DogStatus | null;
  current_location_type?: LocationType | null;
  current_owner_person_id?: number | null;
  public_description?: string | null;
  internal_notes?: string | null;
  public_area?: string | null;
};

export async function updateDog(
  token: string,
  dogId: number,
  payload: DogUpdate
): Promise<Dog> {
  return authPatch<Dog>(`/api/v1/dogs/${dogId}`, token, payload);
}

export async function setDogStatus(
  token: string,
  dogId: number,
  transition: StatusTransition
): Promise<Dog> {
  return authPost<Dog>(`/api/v1/dogs/${dogId}/status`, token, transition);
}

// ============================================================================
// People
// ============================================================================
export async function listPeople(
  token: string,
  params: { offset?: number; limit?: number } = {}
): Promise<Person[]> {
  return authGet<Person[]>(`/api/v1/people${qs(params)}`, token);
}

export async function getPerson(token: string, personId: number): Promise<Person> {
  return authGet<Person>(`/api/v1/people/${personId}`, token);
}

export async function getPersonFile(token: string, personId: number): Promise<PersonFile> {
  return authGet<PersonFile>(`/api/v1/people/${personId}/file`, token);
}

// ============================================================================
// Surrender cases
// ============================================================================
export async function listSurrenderCases(
  token: string,
  params: { status?: SurrenderStatus; offset?: number; limit?: number } = {}
): Promise<SurrenderCase[]> {
  return authGet<SurrenderCase[]>(`/api/v1/surrender-cases${qs(params)}`, token);
}

export async function getSurrenderCase(
  token: string,
  caseId: number
): Promise<SurrenderCase> {
  return authGet<SurrenderCase>(`/api/v1/surrender-cases/${caseId}`, token);
}

export async function activateHomeSubscription(
  token: string,
  caseId: number
): Promise<SurrenderCase> {
  return authPost<SurrenderCase>(
    `/api/v1/surrender-cases/${caseId}/activate-home-subscription`,
    token
  );
}

export async function chargeSurrenderMonth(
  token: string,
  caseId: number
): Promise<SubscriptionPayment> {
  return authPost<SubscriptionPayment>(
    `/api/v1/surrender-cases/${caseId}/charge-month`,
    token
  );
}

export async function listSurrenderPayments(
  token: string,
  caseId: number
): Promise<SubscriptionPayment[]> {
  return authGet<SubscriptionPayment[]>(
    `/api/v1/surrender-cases/${caseId}/payments`,
    token
  );
}

export async function startFacilityTransfer(
  token: string,
  caseId: number
): Promise<StartFacilityTransferResponse> {
  return authPost<StartFacilityTransferResponse>(
    `/api/v1/surrender-cases/${caseId}/start-facility-transfer`,
    token
  );
}

export async function convertToFacility(
  token: string,
  caseId: number
): Promise<ConvertToFacilityResponse> {
  return authPost<ConvertToFacilityResponse>(
    `/api/v1/surrender-cases/${caseId}/convert-to-facility`,
    token
  );
}

// ============================================================================
// Adoption leads
// ============================================================================
export async function listAdoptionLeads(
  token: string,
  params: { offset?: number; limit?: number } = {}
): Promise<AdoptionLead[]> {
  return authGet<AdoptionLead[]>(`/api/v1/adoption-leads${qs(params)}`, token);
}

export type AdoptionLeadCreate = {
  person_id: number;
  dog_id?: number | null;
  preferred_size?: DogSize | null;
  preferred_breed?: string | null;
  has_children?: boolean | null;
  has_other_dogs?: boolean | null;
  home_type?: string | null;
  experience_level?: string | null;
  hours_alone?: string | null;
  consent_messages?: boolean;
  consent_privacy?: boolean;
  source?: string | null;
  notes?: string | null;
};

export async function createAdoptionLead(
  token: string,
  payload: AdoptionLeadCreate
): Promise<AdoptionLead> {
  return authPost<AdoptionLead>("/api/v1/adoption-leads", token, payload);
}

// ============================================================================
// Adoption cases
// ============================================================================
export async function listAdoptionCases(
  token: string,
  params: { status?: AdoptionStatus; offset?: number; limit?: number } = {}
): Promise<AdoptionCase[]> {
  return authGet<AdoptionCase[]>(`/api/v1/adoption-cases${qs(params)}`, token);
}

export async function getAdoptionCase(
  token: string,
  caseId: number
): Promise<AdoptionCase> {
  return authGet<AdoptionCase>(`/api/v1/adoption-cases/${caseId}`, token);
}

export type AdoptionCaseCreate = {
  dog_id: number;
  adopter_person_id: number;
  surrender_case_id?: number | null;
  adoption_lead_id?: number | null;
  is_direct_home_adoption?: boolean;
  meeting_date?: string | null;
};

export async function createAdoptionCase(
  token: string,
  payload: AdoptionCaseCreate
): Promise<AdoptionCase> {
  return authPost<AdoptionCase>("/api/v1/adoption-cases", token, payload);
}

export async function approveAdoptionCase(
  token: string,
  caseId: number
): Promise<AdoptionCase> {
  return authPost<AdoptionCase>(`/api/v1/adoption-cases/${caseId}/approve`, token);
}

export async function completeAdoptionCase(
  token: string,
  caseId: number
): Promise<AdoptionCase> {
  return authPost<AdoptionCase>(`/api/v1/adoption-cases/${caseId}/complete`, token);
}

export async function setAdoptionCaseStatus(
  token: string,
  caseId: number,
  transition: StatusTransition
): Promise<AdoptionCase> {
  return authPost<AdoptionCase>(
    `/api/v1/adoption-cases/${caseId}/status`,
    token,
    transition
  );
}

// ============================================================================
// Ownership transfers
// ============================================================================
export async function listOwnershipTransfers(
  token: string,
  params: { offset?: number; limit?: number } = {}
): Promise<OwnershipTransfer[]> {
  return authGet<OwnershipTransfer[]>(`/api/v1/ownership-transfers${qs(params)}`, token);
}

export async function getOwnershipTransfer(
  token: string,
  transferId: number
): Promise<OwnershipTransfer> {
  return authGet<OwnershipTransfer>(`/api/v1/ownership-transfers/${transferId}`, token);
}

export async function getOwnershipTransferRequiredDocuments(
  token: string,
  transferId: number
): Promise<RequiredDocumentsResponse> {
  return authGet<RequiredDocumentsResponse>(
    `/api/v1/ownership-transfers/${transferId}/required-documents`,
    token
  );
}

export async function getOwnershipTransferDetail(
  token: string,
  transferId: number
): Promise<OwnershipTransferDetail> {
  return authGet<OwnershipTransferDetail>(
    `/api/v1/ownership-transfers/${transferId}/detail`,
    token
  );
}

export async function sendTransferToAuthority(
  token: string,
  transferId: number
): Promise<OwnershipTransfer> {
  return authPost<OwnershipTransfer>(
    `/api/v1/ownership-transfers/${transferId}/send-to-authority`,
    token
  );
}

export async function confirmTransfer(
  token: string,
  transferId: number
): Promise<OwnershipTransfer> {
  return authPost<OwnershipTransfer>(
    `/api/v1/ownership-transfers/${transferId}/confirm`,
    token
  );
}

export async function stopTransfer(
  token: string,
  transferId: number
): Promise<OwnershipTransfer> {
  return authPost<OwnershipTransfer>(
    `/api/v1/ownership-transfers/${transferId}/stop`,
    token
  );
}

export async function runTransferFollowups(
  token: string
): Promise<RunFollowupsResponse> {
  return authPost<RunFollowupsResponse>(
    "/api/v1/ownership-transfers/run-followups",
    token
  );
}

// ============================================================================
// Documents
// ============================================================================
export async function listDocuments(
  token: string,
  params: {
    entity_type?: EntityType;
    entity_id?: number;
    offset?: number;
    limit?: number;
  } = {}
): Promise<DocumentRecord[]> {
  return authGet<DocumentRecord[]>(`/api/v1/documents${qs(params)}`, token);
}

export async function getDocument(
  token: string,
  documentId: number
): Promise<DocumentRecord> {
  return authGet<DocumentRecord>(`/api/v1/documents/${documentId}`, token);
}

export async function uploadDocument(
  token: string,
  args: {
    file: File | Blob;
    related_entity_type: EntityType;
    related_entity_id: number;
    document_type: DocumentType;
    is_sensitive?: boolean;
  }
): Promise<DocumentRecord> {
  const form = new FormData();
  form.append("file", args.file);
  form.append("related_entity_type", args.related_entity_type);
  form.append("related_entity_id", String(args.related_entity_id));
  form.append("document_type", args.document_type);
  form.append("is_sensitive", String(args.is_sensitive ?? false));
  return authUpload<DocumentRecord>("/api/v1/documents/upload", token, form);
}

// ============================================================================
// Signatures
// ============================================================================
export async function listSignatures(
  token: string,
  params: { entity_type?: EntityType; entity_id?: number } = {}
): Promise<SignatureRequest[]> {
  return authGet<SignatureRequest[]>(`/api/v1/signatures${qs(params)}`, token);
}

export async function getSignature(
  token: string,
  signatureId: number
): Promise<SignatureRequest> {
  return authGet<SignatureRequest>(`/api/v1/signatures/${signatureId}`, token);
}

export async function markSignatureSigned(
  token: string,
  signatureId: number
): Promise<SignatureRequest> {
  return authPost<SignatureRequest>(
    `/api/v1/signatures/${signatureId}/mark-signed`,
    token
  );
}

// ============================================================================
// Authorities (municipalities) + localities directory
// ============================================================================
export async function listMunicipalities(
  token: string,
  params: { offset?: number; limit?: number } = {}
): Promise<Municipality[]> {
  return authGet<Municipality[]>(`/api/v1/municipalities${qs({ limit: 500, ...params })}`, token);
}

export type MunicipalityUpdate = {
  city_name?: string | null;
  authority_name?: string | null;
  district?: string | null;
  vet_department_name?: string | null;
  vet_name?: string | null;
  license_number?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  notes?: string | null;
  is_active?: boolean;
};

export async function updateMunicipality(
  token: string,
  id: number,
  payload: MunicipalityUpdate
): Promise<Municipality> {
  return authPatch<Municipality>(`/api/v1/municipalities/${id}`, token, payload);
}

export type MunicipalityCreate = {
  city_name: string;
  authority_name?: string | null;
  district?: string | null;
  vet_name?: string | null;
  license_number?: string | null;
  email?: string | null;
  phone?: string | null;
};

export async function createMunicipality(
  token: string,
  payload: MunicipalityCreate
): Promise<Municipality> {
  return authPost<Municipality>("/api/v1/municipalities", token, payload);
}

export async function listLocalities(
  token: string,
  params: { search?: string; needs_review?: boolean; offset?: number; limit?: number } = {}
): Promise<LocalityListResponse> {
  return authGet<LocalityListResponse>(`/api/v1/localities${qs(params)}`, token);
}

export async function resolveLocality(
  token: string,
  city: string
): Promise<LocalityResolveResponse> {
  return authGet<LocalityResolveResponse>(`/api/v1/localities/resolve${qs({ city })}`, token);
}

export async function assignLocality(
  token: string,
  localityId: number,
  payload: { municipality_id?: number | null; needs_review?: boolean | null }
): Promise<Locality> {
  return authPatch<Locality>(`/api/v1/localities/${localityId}`, token, payload);
}

// ============================================================================
// Integrations — outbound email settings (admin)
// ============================================================================
export type EmailSettings = {
  provider: string;
  host: string;
  port: number;
  use_tls: boolean;
  username: string | null;
  from_name: string | null;
  from_email: string | null;
  enabled: boolean;
  password_set: boolean;
  updated_at: string;
};

export type EmailSettingsUpdate = {
  host?: string;
  port?: number;
  use_tls?: boolean;
  username?: string | null;
  // Write-only: send a value to set/replace, "" to clear, omit to keep.
  password?: string | null;
  from_name?: string | null;
  from_email?: string | null;
  enabled?: boolean;
};

export type EmailTestResult = { status: string; detail: string };

export async function getEmailSettings(token: string): Promise<EmailSettings> {
  return authGet<EmailSettings>("/api/v1/integrations/email", token);
}

export async function updateEmailSettings(
  token: string,
  payload: EmailSettingsUpdate
): Promise<EmailSettings> {
  return authPut<EmailSettings>("/api/v1/integrations/email", token, payload);
}

export async function sendTestEmail(
  token: string,
  to: string
): Promise<EmailTestResult> {
  return authPost<EmailTestResult>("/api/v1/integrations/email/test", token, { to });
}

// ============================================================================
// QR links
// ============================================================================
export async function getQrLinks(
  token: string,
  dogId?: number
): Promise<QrLinks> {
  return authGet<QrLinks>(`/api/v1/qr/links${qs({ dog_id: dogId })}`, token);
}
