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
  generateTransferForm,
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
  formatDateTime,
} from "../../_components/ui";
import {
  ownershipTransferStatusLabels,
  transferTypeLabels,
  signatureStatusLabels,
  signatureTypeLabels,
} from "../../_components/labels";
import DocumentsManager from "../../_components/DocumentsManager";
import WorkflowProgress from "../../_components/WorkflowProgress";

const TRANSFER_DOC_TYPES: DocumentType[] = [
  "ownership_transfer_form",
  "id_card_surrenderer",
  "receiver_approval_form",
  "id_card_receiver",
  "adopter_with_dog_photo",
  "authority_submission",
  "authority_confirmation",
  "other",
];

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

          <WorkflowProgress token={token!} transferId={transferId} onChanged={load} />

          <DocumentsManager
            token={token!}
            entityType="ownership_transfer"
            entityId={transferId}
            uploadTypes={TRANSFER_DOC_TYPES}
            required={data.required_documents}
            documentsComplete={data.documents_complete}
            generate={{ label: "הפקת טופס העברה", run: () => generateTransferForm(token!, transferId) }}
            onChanged={load}
          />

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
