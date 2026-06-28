"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getOwnershipTransferDetail,
  sendTransferToAuthority,
  confirmTransfer,
  stopTransfer,
  runTransferFollowups,
  type OwnershipTransferDetail,
  type DocumentType,
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
  formatDateTime,
} from "../../_components/ui";
import {
  ownershipTransferStatusLabels,
  transferTypeLabels,
  documentTypeLabels,
  documentStatusLabels,
  signatureStatusLabels,
  signatureTypeLabels,
} from "../../_components/labels";

function docTypeLabel(value: string): string {
  return documentTypeLabels[value as DocumentType] ?? value;
}

export default function OwnershipTransferDetailPage() {
  const token = useAdminToken();
  const params = useParams<{ id: string }>();
  const transferId = Number(params.id);

  const [data, setData] = useState<OwnershipTransferDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const d = await getOwnershipTransferDetail(token, transferId);
      setData(d);
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }, [token, transferId]);

  useEffect(() => {
    load();
  }, [load]);

  async function runAction(fn: () => Promise<unknown>, successMsg: string) {
    if (!token) return;
    setNotice(null);
    setError(null);
    try {
      await fn();
      setNotice(successMsg);
      await load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  if (!data && !error) return <Spinner />;

  // Which required document types already have an uploaded/approved record.
  const presentDocTypes = new Set(
    (data?.documents ?? [])
      .filter((d) => d.status === "uploaded" || d.status === "approved")
      .map((d) => d.document_type as string)
  );

  const transfer = data?.transfer;
  const timeline: { label: string; value: string | null | undefined }[] = transfer
    ? [
        { label: "נוצר", value: transfer.created_at },
        { label: "נשלח לרשות", value: transfer.sent_to_authority_at },
        { label: "מעקב אחרון", value: transfer.last_followup_at },
        { label: "מעקב הבא", value: transfer.next_followup_at },
        { label: "אושר", value: transfer.confirmed_at },
      ]
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={`העברת בעלות #${transferId}`}
        action={
          <Link href="/admin/ownership-transfers" className="btn-outline text-sm">
            חזרה לרשימה
          </Link>
        }
      />

      {error && <ErrorBox message={error} />}
      {notice && <div className="card border-green-200 bg-green-50 text-sm text-green-700">{notice}</div>}

      {data && transfer && (
        <>
          <div className="card space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-brand-dark">פרטי ההעברה</h2>
              <Badge>{ownershipTransferStatusLabels[transfer.status]}</Badge>
            </div>
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <Field label="סוג העברה">{transferTypeLabels[transfer.transfer_type]}</Field>
              <Field label="כלב">
                {data.dog ? (
                  <Link href={`/admin/dogs/${data.dog.id}`} className="text-brand hover:underline">
                    {data.dog.name ? `${data.dog.name} (#${data.dog.id})` : `כלב #${data.dog.id}`}
                  </Link>
                ) : (
                  "—"
                )}
              </Field>
              <Field label="מוסר">
                {data.from_person
                  ? `${data.from_person.first_name} ${data.from_person.last_name ?? ""}`.trim()
                  : "—"}
              </Field>
              <Field label="מקבל">
                {data.to_person
                  ? `${data.to_person.first_name} ${data.to_person.last_name ?? ""}`.trim()
                  : "—"}
              </Field>
              <Field label="רשות מוסרת">{data.from_authority_name}</Field>
              <Field label="רשות מקבלת">{data.to_authority_name}</Field>
              <Field label="הערות">{transfer.notes}</Field>
            </dl>
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">פעולות</h2>
            <div className="flex flex-wrap gap-2">
              <ActionButton
                onClick={() => runAction(() => sendTransferToAuthority(token!, transferId), "נשלח לרשות")}
              >
                שליחה לרשות
              </ActionButton>
              <ActionButton
                variant="outline"
                onClick={() => runAction(() => confirmTransfer(token!, transferId), "ההעברה אושרה")}
              >
                אישור העברה
              </ActionButton>
              <ActionButton
                variant="outline"
                onClick={() => runAction(() => runTransferFollowups(token!), "מעקבים הורצו")}
              >
                הרצת מעקבים
              </ActionButton>
              <ActionButton
                variant="danger"
                onClick={() => runAction(() => stopTransfer(token!, transferId), "ההעברה הופסקה")}
              >
                הפסקת העברה
              </ActionButton>
            </div>
          </div>

          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-brand-dark">מסמכים נדרשים</h2>
              <Badge tone={data.documents_complete ? "green" : "amber"}>
                {data.documents_complete ? "כל המסמכים הושלמו" : "חסרים מסמכים"}
              </Badge>
            </div>
            {data.required_documents.length === 0 ? (
              <p className="text-sm text-gray-500">אין מסמכים נדרשים.</p>
            ) : (
              <ul className="space-y-1 text-sm">
                {data.required_documents.map((dt) => {
                  const present = presentDocTypes.has(dt);
                  return (
                    <li key={dt} className="flex items-center gap-2">
                      <span className={present ? "text-green-600" : "text-gray-400"}>
                        {present ? "✓" : "○"}
                      </span>
                      <span>{docTypeLabel(dt)}</span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">ציר זמן סטטוס</h2>
            <ol className="space-y-2 text-sm">
              {timeline.map((t) => (
                <li key={t.label} className="flex items-center gap-3">
                  <span className={`h-2 w-2 rounded-full ${t.value ? "bg-brand" : "bg-gray-300"}`} />
                  <span className="w-28 text-gray-500">{t.label}</span>
                  <span className="text-gray-900">{formatDateTime(t.value)}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">כל המסמכים</h2>
            {data.documents.length === 0 ? (
              <p className="text-sm text-gray-500">אין מסמכים.</p>
            ) : (
              <ul className="space-y-1 text-sm">
                {data.documents.map((d) => (
                  <li key={d.id} className="flex items-center gap-2">
                    <span>{docTypeLabel(d.document_type)}</span>
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

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">חתימות</h2>
            {data.signature_requests.length === 0 ? (
              <p className="text-sm text-gray-500">אין בקשות חתימה.</p>
            ) : (
              <ul className="space-y-1 text-sm">
                {data.signature_requests.map((s) => (
                  <li key={s.id} className="flex items-center gap-2">
                    <span>{signatureTypeLabels[s.signature_type]}</span>
                    <span className="text-gray-500">#{s.signer_person_id}</span>
                    <Badge tone={s.status === "signed" ? "green" : "amber"}>{signatureStatusLabels[s.status]}</Badge>
                    <span className="text-gray-400">{formatDateTime(s.signed_at)}</span>
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
