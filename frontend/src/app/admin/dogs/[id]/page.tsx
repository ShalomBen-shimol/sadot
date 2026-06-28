"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getDogFile,
  updateDog,
  setDogStatus,
  type DogFile,
  type DogStatus,
  type DogUpdate,
} from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  Badge,
  ActionButton,
  Field,
  formatDate,
} from "../../_components/ui";
import {
  dogStatusLabels,
  dogGenderLabels,
  dogSizeLabels,
  locationTypeLabels,
  surrenderStatusLabels,
  adoptionStatusLabels,
  ownershipTransferStatusLabels,
  documentTypeLabels,
  documentStatusLabels,
} from "../../_components/labels";

const STATUS_OPTIONS = Object.entries(dogStatusLabels) as [DogStatus, string][];

type BasicsForm = {
  name: string;
  breed: string;
  age: string;
  color: string;
  chip_number: string;
  public_area: string;
  public_description: string;
  internal_notes: string;
  medical_notes: string;
  behavior_notes: string;
};

export default function DogDetail() {
  const token = useAdminToken();
  const params = useParams<{ id: string }>();
  const dogId = Number(params.id);

  const [file, setFile] = useState<DogFile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [nextStatus, setNextStatus] = useState<DogStatus | "">("");
  const [form, setForm] = useState<BasicsForm | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const f = await getDogFile(token, dogId);
      setFile(f);
      setNextStatus(f.dog.status);
      setForm({
        name: f.dog.name ?? "",
        breed: f.dog.breed ?? "",
        age: f.dog.age === null ? "" : String(f.dog.age),
        color: f.dog.color ?? "",
        chip_number: f.dog.chip_number ?? "",
        public_area: f.dog.public_area ?? "",
        public_description: f.dog.public_description ?? "",
        internal_notes: f.dog.internal_notes ?? "",
        medical_notes: f.dog.medical_notes ?? "",
        behavior_notes: f.dog.behavior_notes ?? "",
      });
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }, [token, dogId]);

  useEffect(() => {
    load();
  }, [load]);

  function setField<K extends keyof BasicsForm>(key: K, value: string) {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function saveBasics() {
    if (!token || !form) return;
    setNotice(null);
    setError(null);
    const trimmedAge = form.age.trim();
    const payload: DogUpdate = {
      name: form.name.trim() || null,
      breed: form.breed.trim() || null,
      age: trimmedAge === "" ? null : Number(trimmedAge),
      color: form.color.trim() || null,
      chip_number: form.chip_number.trim() || null,
      public_area: form.public_area.trim() || null,
      public_description: form.public_description.trim() || null,
      internal_notes: form.internal_notes.trim() || null,
      medical_notes: form.medical_notes.trim() || null,
      behavior_notes: form.behavior_notes.trim() || null,
    };
    try {
      await updateDog(token, dogId, payload);
      setNotice("הפרטים נשמרו");
      await load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  async function changeStatus() {
    if (!token || !nextStatus) return;
    setNotice(null);
    setError(null);
    try {
      await setDogStatus(token, dogId, { status: nextStatus });
      setNotice("הסטטוס עודכן");
      await load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  if (!file && !error) return <Spinner />;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`תיק כלב #${dogId}${file?.dog.name ? ` — ${file.dog.name}` : ""}`}
        action={
          <Link href="/admin/dogs" className="btn-outline text-sm">
            חזרה לרשימה
          </Link>
        }
      />

      {error && <ErrorBox message={error} />}
      {notice && <div className="card border-green-200 bg-green-50 text-sm text-green-700">{notice}</div>}

      {file && (
        <>
          <div className="card space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-brand-dark">סקירה</h2>
              <Badge>{dogStatusLabels[file.dog.status]}</Badge>
            </div>
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <Field label="מין">{dogGenderLabels[file.dog.gender]}</Field>
              <Field label="גודל">{file.dog.size ? dogSizeLabels[file.dog.size] : "—"}</Field>
              <Field label="מיקום נוכחי">{locationTypeLabels[file.dog.current_location_type]}</Field>
              <Field label="מסורס/ת">{file.dog.is_neutered === null ? "—" : file.dog.is_neutered ? "כן" : "לא"}</Field>
              <Field label="מחוסן/ת">{file.dog.is_vaccinated === null ? "—" : file.dog.is_vaccinated ? "כן" : "לא"}</Field>
              <Field label="בעלים נוכחי">
                {file.current_owner
                  ? `${file.current_owner.first_name} ${file.current_owner.last_name ?? ""}`.trim()
                  : "—"}
              </Field>
            </dl>
          </div>

          {form && (
            <div className="card space-y-4">
              <h2 className="text-lg font-semibold text-brand-dark">עריכת פרטים</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="label">שם</label>
                  <input className="input" value={form.name} onChange={(e) => setField("name", e.target.value)} />
                </div>
                <div>
                  <label className="label">גזע</label>
                  <input className="input" value={form.breed} onChange={(e) => setField("breed", e.target.value)} />
                </div>
                <div>
                  <label className="label">גיל (שנים)</label>
                  <input
                    className="input"
                    type="number"
                    step="0.1"
                    min="0"
                    value={form.age}
                    onChange={(e) => setField("age", e.target.value)}
                  />
                </div>
                <div>
                  <label className="label">צבע</label>
                  <input className="input" value={form.color} onChange={(e) => setField("color", e.target.value)} />
                </div>
                <div>
                  <label className="label">מספר שבב</label>
                  <input
                    className="input"
                    value={form.chip_number}
                    onChange={(e) => setField("chip_number", e.target.value)}
                  />
                </div>
                <div>
                  <label className="label">אזור (פומבי)</label>
                  <input
                    className="input"
                    value={form.public_area}
                    onChange={(e) => setField("public_area", e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="label">תיאור פומבי</label>
                <textarea
                  className="input"
                  rows={3}
                  value={form.public_description}
                  onChange={(e) => setField("public_description", e.target.value)}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="label">הערות רפואיות</label>
                  <textarea
                    className="input"
                    rows={2}
                    value={form.medical_notes}
                    onChange={(e) => setField("medical_notes", e.target.value)}
                  />
                </div>
                <div>
                  <label className="label">הערות התנהגות</label>
                  <textarea
                    className="input"
                    rows={2}
                    value={form.behavior_notes}
                    onChange={(e) => setField("behavior_notes", e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="label">הערות פנימיות</label>
                <textarea
                  className="input"
                  rows={2}
                  value={form.internal_notes}
                  onChange={(e) => setField("internal_notes", e.target.value)}
                />
              </div>
              <ActionButton onClick={saveBasics}>שמירת פרטים</ActionButton>
            </div>
          )}

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">שינוי סטטוס</h2>
            <div className="flex flex-wrap items-end gap-2">
              <select
                className="input max-w-xs"
                value={nextStatus}
                onChange={(e) => setNextStatus(e.target.value as DogStatus | "")}
              >
                {STATUS_OPTIONS.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
              <ActionButton variant="outline" disabled={nextStatus === file.dog.status} onClick={changeStatus}>
                עדכון סטטוס
              </ActionButton>
            </div>
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">תיקים מקושרים</h2>
            <div className="grid gap-4 sm:grid-cols-3">
              <div>
                <div className="text-xs text-gray-500">תיקי מסירה</div>
                {file.surrender_cases.length === 0 ? (
                  <p className="text-sm text-gray-400">אין</p>
                ) : (
                  <ul className="mt-1 space-y-1 text-sm">
                    {file.surrender_cases.map((c) => (
                      <li key={c.id}>
                        <Link href={`/admin/surrender-cases/${c.id}`} className="text-brand hover:underline">
                          #{c.id}
                        </Link>{" "}
                        <span className="text-gray-500">({surrenderStatusLabels[c.status]})</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <div className="text-xs text-gray-500">תיקי אימוץ</div>
                {file.adoption_cases.length === 0 ? (
                  <p className="text-sm text-gray-400">אין</p>
                ) : (
                  <ul className="mt-1 space-y-1 text-sm">
                    {file.adoption_cases.map((c) => (
                      <li key={c.id}>
                        <Link href={`/admin/adoption-cases/${c.id}`} className="text-brand hover:underline">
                          #{c.id}
                        </Link>{" "}
                        <span className="text-gray-500">({adoptionStatusLabels[c.status]})</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div>
                <div className="text-xs text-gray-500">העברות בעלות</div>
                {file.ownership_transfers.length === 0 ? (
                  <p className="text-sm text-gray-400">אין</p>
                ) : (
                  <ul className="mt-1 space-y-1 text-sm">
                    {file.ownership_transfers.map((t) => (
                      <li key={t.id}>
                        <Link href={`/admin/ownership-transfers/${t.id}`} className="text-brand hover:underline">
                          #{t.id}
                        </Link>{" "}
                        <span className="text-gray-500">({ownershipTransferStatusLabels[t.status]})</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">מסמכים</h2>
            {file.documents.length === 0 ? (
              <p className="text-sm text-gray-500">אין מסמכים.</p>
            ) : (
              <ul className="space-y-1 text-sm">
                {file.documents.map((d) => (
                  <li key={d.id} className="flex items-center gap-2">
                    <span>{documentTypeLabels[d.document_type]}</span>
                    <Badge tone={d.status === "approved" ? "green" : "gray"}>{documentStatusLabels[d.status]}</Badge>
                    {d.file_url && (
                      <a href={d.file_url} target="_blank" rel="noreferrer" className="text-brand hover:underline">
                        צפייה
                      </a>
                    )}
                    <span className="text-gray-400">{formatDate(d.created_at)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
