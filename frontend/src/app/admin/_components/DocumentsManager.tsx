"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  listDocuments,
  uploadDocument,
  approveDocument,
  rejectDocument,
  type DocumentRecord,
  type DocumentType,
  type EntityType,
} from "@/lib/api";
import { ActionButton, Badge, ErrorBox } from "./ui";
import { documentTypeLabels, documentStatusLabels } from "./labels";

function docTypeLabel(value: string): string {
  return documentTypeLabels[value as DocumentType] ?? value;
}

// Document types that hold sensitive PII (ID photos, signed forms).
const SENSITIVE = /(_form$|^id_card_)/;

type Props = {
  token: string;
  entityType: EntityType;
  entityId: number;
  // Options offered in the manual-upload picker.
  uploadTypes: DocumentType[];
  // Optional required-documents checklist (doc-type string values).
  required?: string[];
  documentsComplete?: boolean;
  // Optional "generate signable form" action.
  generate?: { label: string; run: () => Promise<unknown> };
  // Notify the parent (e.g. to reload its own detail) after any change.
  onChanged?: () => void;
};

export default function DocumentsManager({
  token,
  entityType,
  entityId,
  uploadTypes,
  required,
  documentsComplete,
  generate,
  onChanged,
}: Props) {
  const [docs, setDocs] = useState<DocumentRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadType, setUploadType] = useState<DocumentType>(uploadTypes[0]);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try {
      setDocs(await listDocuments(token, { entity_type: entityType, entity_id: entityId }));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "שגיאה בטעינת מסמכים");
    }
  }, [token, entityType, entityId]);

  useEffect(() => {
    load();
  }, [load]);

  async function act(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      await load();
      onChanged?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "הפעולה נכשלה");
    }
  }

  async function onFilePicked(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-picking the same file
    if (!file) return;
    await act(() =>
      uploadDocument(token, {
        file,
        related_entity_type: entityType,
        related_entity_id: entityId,
        document_type: uploadType,
        is_sensitive: SENSITIVE.test(uploadType),
      })
    );
  }

  const present = new Set(
    (docs ?? [])
      .filter((d) => d.status === "uploaded" || d.status === "approved")
      .map((d) => d.document_type as string)
  );

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-brand-dark">מסמכים</h2>
        {documentsComplete !== undefined && (
          <Badge tone={documentsComplete ? "green" : "amber"}>
            {documentsComplete ? "כל המסמכים הושלמו" : "חסרים מסמכים"}
          </Badge>
        )}
      </div>

      {error && <ErrorBox message={error} />}

      {/* Required checklist */}
      {required && required.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-medium text-gray-500">נדרשים</p>
          <ul className="space-y-1 text-sm">
            {required.map((dt) => {
              const ok = present.has(dt);
              return (
                <li key={dt} className="flex items-center gap-2">
                  <span className={ok ? "text-green-600" : "text-gray-400"}>{ok ? "✓" : "○"}</span>
                  <span className={ok ? "text-gray-900" : "text-gray-600"}>{docTypeLabel(dt)}</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Uploaded documents + actions */}
      <div>
        <p className="mb-1 text-xs font-medium text-gray-500">מסמכים שהתקבלו</p>
        {docs === null ? (
          <p className="text-sm text-gray-400">טוען…</p>
        ) : docs.length === 0 ? (
          <p className="text-sm text-gray-500">אין מסמכים עדיין.</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {docs.map((d) => (
              <li key={d.id} className="flex flex-wrap items-center gap-2 py-2 text-sm">
                <span className="font-medium text-gray-900">{docTypeLabel(d.document_type)}</span>
                {d.is_sensitive && <Badge tone="red">רגיש</Badge>}
                <Badge tone={d.status === "approved" ? "green" : d.status === "rejected" ? "red" : "gray"}>
                  {documentStatusLabels[d.status]}
                </Badge>
                {d.file_url && (
                  <a href={d.file_url} target="_blank" rel="noreferrer" className="text-brand hover:underline">
                    צפייה
                  </a>
                )}
                <span className="ml-auto flex gap-2">
                  {d.status !== "approved" && (
                    <button
                      onClick={() => act(() => approveDocument(token, d.id))}
                      className="text-xs text-green-700 hover:underline"
                    >
                      אישור
                    </button>
                  )}
                  {d.status !== "rejected" && (
                    <button
                      onClick={() => act(() => rejectDocument(token, d.id))}
                      className="text-xs text-red-600 hover:underline"
                    >
                      דחייה
                    </button>
                  )}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Upload + generate actions */}
      <div className="flex flex-wrap items-center gap-2 border-t border-gray-100 pt-3">
        <select
          className="input max-w-xs"
          value={uploadType}
          onChange={(e) => setUploadType(e.target.value as DocumentType)}
        >
          {uploadTypes.map((t) => (
            <option key={t} value={t}>
              {docTypeLabel(t)}
            </option>
          ))}
        </select>
        <button className="btn-outline text-sm" onClick={() => fileRef.current?.click()}>
          העלאת קובץ
        </button>
        <input ref={fileRef} type="file" accept="image/*,application/pdf" className="hidden" onChange={onFilePicked} />
        {generate && <ActionButton onClick={() => act(generate.run)}>{generate.label}</ActionButton>}
      </div>
    </div>
  );
}
