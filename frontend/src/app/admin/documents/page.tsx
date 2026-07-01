"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  listDocuments,
  approveDocument,
  rejectDocument,
  type DocumentRecord,
  type DocumentType,
  type DocumentStatus,
  type EntityType,
} from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  Badge,
  formatDateTime,
} from "../_components/ui";
import {
  documentTypeLabels,
  documentStatusLabels,
  entityTypeLabels,
} from "../_components/labels";

// Entity types that have a back-office detail page we can deep-link to.
const ENTITY_ROUTES: Partial<Record<EntityType, string>> = {
  dog: "/admin/dogs",
  ownership_transfer: "/admin/ownership-transfers",
  surrender_case: "/admin/surrender-cases",
  adoption_case: "/admin/adoption-cases",
};

const DOC_TYPES: DocumentType[] = [
  "surrender_form",
  "ownership_transfer_form",
  "receiver_approval_form",
  "id_card_surrenderer",
  "id_card_receiver",
  "adopter_with_dog_photo",
  "authority_submission",
  "authority_confirmation",
  "other",
];

const STATUSES: DocumentStatus[] = ["pending", "uploaded", "approved", "rejected"];

const ENTITY_TYPES: EntityType[] = [
  "dog",
  "person",
  "surrender_case",
  "adoption_case",
  "adoption_lead",
  "ownership_transfer",
];

function statusTone(s: DocumentStatus): "green" | "red" | "amber" | "gray" {
  if (s === "approved") return "green";
  if (s === "rejected") return "red";
  if (s === "uploaded") return "amber";
  return "gray";
}

function EntityLink({ doc }: { doc: DocumentRecord }) {
  const base = ENTITY_ROUTES[doc.related_entity_type];
  const label = `${entityTypeLabels[doc.related_entity_type]} #${doc.related_entity_id}`;
  if (!base) return <span className="text-gray-600">{label}</span>;
  return (
    <Link href={`${base}/${doc.related_entity_id}`} className="text-brand hover:underline">
      {label}
    </Link>
  );
}

export default function DocumentsConsolePage() {
  const token = useAdminToken();
  const [docs, setDocs] = useState<DocumentRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [entityType, setEntityType] = useState<EntityType | "">("");
  const [docType, setDocType] = useState<DocumentType | "">("");
  const [status, setStatus] = useState<DocumentStatus | "">("");
  const [sensitiveOnly, setSensitiveOnly] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const rows = await listDocuments(token, {
        entity_type: entityType || undefined,
        document_type: docType || undefined,
        status: status || undefined,
        is_sensitive: sensitiveOnly || undefined,
        limit: 500,
      });
      // Newest first (the API returns insertion order).
      rows.sort((a, b) => b.id - a.id);
      setDocs(rows);
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }, [token, entityType, docType, status, sensitiveOnly]);

  useEffect(() => {
    load();
  }, [load]);

  async function act(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      await load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  function reset() {
    setEntityType("");
    setDocType("");
    setStatus("");
    setSensitiveOnly(false);
  }

  if (token === undefined) return <Spinner />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="ניהול מסמכים"
        subtitle="כל המסמכים במערכת במקום אחד — סינון, צפייה ואישור/דחייה."
        action={docs && <span className="text-xs text-gray-400">{docs.length} מסמכים</span>}
      />

      {error && <ErrorBox message={error} />}

      {/* Filters */}
      <div className="card flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="mb-1 block text-xs text-gray-500">סוג ישות</span>
          <select
            className="input"
            value={entityType}
            onChange={(e) => setEntityType(e.target.value as EntityType | "")}
          >
            <option value="">הכל</option>
            {ENTITY_TYPES.map((t) => (
              <option key={t} value={t}>
                {entityTypeLabels[t]}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs text-gray-500">סוג מסמך</span>
          <select
            className="input"
            value={docType}
            onChange={(e) => setDocType(e.target.value as DocumentType | "")}
          >
            <option value="">הכל</option>
            {DOC_TYPES.map((t) => (
              <option key={t} value={t}>
                {documentTypeLabels[t]}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs text-gray-500">סטטוס</span>
          <select
            className="input"
            value={status}
            onChange={(e) => setStatus(e.target.value as DocumentStatus | "")}
          >
            <option value="">הכל</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {documentStatusLabels[s]}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 pb-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={sensitiveOnly}
            onChange={(e) => setSensitiveOnly(e.target.checked)}
          />
          רגישים בלבד
        </label>
        <button className="mb-1 text-xs text-gray-500 hover:underline" onClick={reset}>
          איפוס
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto">
        {docs === null ? (
          <Spinner />
        ) : docs.length === 0 ? (
          <p className="py-6 text-center text-sm text-gray-500">אין מסמכים התואמים לסינון.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-right text-xs text-gray-500">
                <th className="py-2 pl-3 font-medium">סוג מסמך</th>
                <th className="py-2 pl-3 font-medium">ישות</th>
                <th className="py-2 pl-3 font-medium">סטטוס</th>
                <th className="py-2 pl-3 font-medium">נוצר</th>
                <th className="py-2 pl-3 font-medium">פעולות</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id} className="border-b border-gray-50 last:border-0">
                  <td className="py-2.5 pl-3">
                    <span className="font-medium text-gray-900">
                      {documentTypeLabels[d.document_type]}
                    </span>
                    {d.is_sensitive && (
                      <span className="mr-2">
                        <Badge tone="red">רגיש</Badge>
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 pl-3">
                    <EntityLink doc={d} />
                  </td>
                  <td className="py-2.5 pl-3">
                    <Badge tone={statusTone(d.status)}>{documentStatusLabels[d.status]}</Badge>
                  </td>
                  <td className="py-2.5 pl-3 text-gray-500">{formatDateTime(d.created_at)}</td>
                  <td className="py-2.5 pl-3">
                    <div className="flex items-center gap-3">
                      {d.file_url && (
                        <a
                          href={d.file_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-brand hover:underline"
                        >
                          צפייה
                        </a>
                      )}
                      {d.status !== "approved" && (
                        <button
                          onClick={() => act(() => approveDocument(token, d.id))}
                          className="text-green-700 hover:underline"
                        >
                          אישור
                        </button>
                      )}
                      {d.status !== "rejected" && (
                        <button
                          onClick={() => act(() => rejectDocument(token, d.id))}
                          className="text-red-600 hover:underline"
                        >
                          דחייה
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
