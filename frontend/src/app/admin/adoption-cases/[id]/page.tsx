"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getAdoptionCase,
  approveAdoptionCase,
  completeAdoptionCase,
  setAdoptionCaseStatus,
  listSignatures,
  listDocuments,
  type AdoptionCase,
  type AdoptionStatus,
  type SignatureRequest,
  type DocumentRecord,
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
  adoptionStatusLabels,
  signatureStatusLabels,
  signatureTypeLabels,
  documentStatusLabels,
  documentTypeLabels,
} from "../../_components/labels";

const STATUS_OPTIONS = Object.entries(adoptionStatusLabels) as [AdoptionStatus, string][];

export default function AdoptionCaseDetail() {
  const token = useAdminToken();
  const params = useParams<{ id: string }>();
  const caseId = Number(params.id);

  const [data, setData] = useState<AdoptionCase | null>(null);
  const [signatures, setSignatures] = useState<SignatureRequest[]>([]);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [nextStatus, setNextStatus] = useState<AdoptionStatus | "">("");

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const [c, sigs, docs] = await Promise.all([
        getAdoptionCase(token, caseId),
        listSignatures(token, { entity_type: "adoption_case", entity_id: caseId }),
        listDocuments(token, { entity_type: "adoption_case", entity_id: caseId }),
      ]);
      setData(c);
      setSignatures(sigs);
      setDocuments(docs);
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }, [token, caseId]);

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

  return (
    <div className="space-y-6">
      <PageHeader
        title={`תיק אימוץ #${caseId}`}
        action={
          <Link href="/admin/adoption-cases" className="btn-outline text-sm">
            חזרה לרשימה
          </Link>
        }
      />

      {error && <ErrorBox message={error} />}
      {notice && <div className="card border-green-200 bg-green-50 text-sm text-green-700">{notice}</div>}

      {data && (
        <>
          <div className="card space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-brand-dark">פרטי התיק</h2>
              <Badge>{adoptionStatusLabels[data.status]}</Badge>
            </div>
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <Field label="כלב">
                <Link href={`/admin/dogs/${data.dog_id}`} className="text-brand hover:underline">
                  כלב #{data.dog_id}
                </Link>
              </Field>
              <Field label="מאמץ (Person ID)">{data.adopter_person_id}</Field>
              <Field label="תיק מסירה מקושר">
                {data.surrender_case_id ? (
                  <Link href={`/admin/surrender-cases/${data.surrender_case_id}`} className="text-brand hover:underline">
                    #{data.surrender_case_id}
                  </Link>
                ) : (
                  "—"
                )}
              </Field>
              <Field label="ליד אימוץ מקושר">{data.adoption_lead_id ?? "—"}</Field>
              <Field label="אימוץ ביתי ישיר">{data.is_direct_home_adoption ? "כן" : "לא"}</Field>
              <Field label="מועד פגישה">{formatDateTime(data.meeting_date)}</Field>
              <Field label="תאריך פתיחה">{formatDate(data.created_at)}</Field>
            </dl>
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">פעולות</h2>
            <div className="flex flex-wrap gap-2">
              <ActionButton onClick={() => runAction(() => approveAdoptionCase(token!, caseId), "התיק אושר")}>
                אישור אימוץ
              </ActionButton>
              <ActionButton
                variant="outline"
                onClick={() => runAction(() => completeAdoptionCase(token!, caseId), "האימוץ הושלם")}
              >
                השלמת אימוץ
              </ActionButton>
            </div>
            <div className="flex flex-wrap items-end gap-2 border-t pt-3">
              <div>
                <label className="label">שינוי סטטוס ידני</label>
                <select
                  className="input max-w-xs"
                  value={nextStatus}
                  onChange={(e) => setNextStatus(e.target.value as AdoptionStatus | "")}
                >
                  <option value="">בחרו סטטוס</option>
                  {STATUS_OPTIONS.map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <ActionButton
                variant="outline"
                disabled={!nextStatus}
                onClick={() =>
                  runAction(
                    () => setAdoptionCaseStatus(token!, caseId, { status: nextStatus as string }),
                    "הסטטוס עודכן"
                  )
                }
              >
                עדכון סטטוס
              </ActionButton>
            </div>
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">חתימות</h2>
            {signatures.length === 0 ? (
              <p className="text-sm text-gray-500">אין בקשות חתימה.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-right text-sm">
                  <thead className="border-b bg-gray-50 text-xs text-gray-500">
                    <tr>
                      <th className="px-3 py-2 font-medium">סוג חותם</th>
                      <th className="px-3 py-2 font-medium">חותם (Person)</th>
                      <th className="px-3 py-2 font-medium">סטטוס</th>
                      <th className="px-3 py-2 font-medium">נחתם בתאריך</th>
                    </tr>
                  </thead>
                  <tbody>
                    {signatures.map((s) => (
                      <tr key={s.id} className="border-b last:border-0">
                        <td className="px-3 py-2">{signatureTypeLabels[s.signature_type]}</td>
                        <td className="px-3 py-2">#{s.signer_person_id}</td>
                        <td className="px-3 py-2">
                          <Badge tone={s.status === "signed" ? "green" : "amber"}>
                            {signatureStatusLabels[s.status]}
                          </Badge>
                        </td>
                        <td className="px-3 py-2">{formatDateTime(s.signed_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">מסמכים</h2>
            {documents.length === 0 ? (
              <p className="text-sm text-gray-500">אין מסמכים.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-right text-sm">
                  <thead className="border-b bg-gray-50 text-xs text-gray-500">
                    <tr>
                      <th className="px-3 py-2 font-medium">סוג מסמך</th>
                      <th className="px-3 py-2 font-medium">סטטוס</th>
                      <th className="px-3 py-2 font-medium">קובץ</th>
                      <th className="px-3 py-2 font-medium">תאריך</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((d) => (
                      <tr key={d.id} className="border-b last:border-0">
                        <td className="px-3 py-2">{documentTypeLabels[d.document_type]}</td>
                        <td className="px-3 py-2">
                          <Badge tone={d.status === "approved" ? "green" : "gray"}>
                            {documentStatusLabels[d.status]}
                          </Badge>
                        </td>
                        <td className="px-3 py-2">
                          {d.file_url ? (
                            <a href={d.file_url} target="_blank" rel="noreferrer" className="text-brand hover:underline">
                              צפייה
                            </a>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="px-3 py-2">{formatDate(d.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
