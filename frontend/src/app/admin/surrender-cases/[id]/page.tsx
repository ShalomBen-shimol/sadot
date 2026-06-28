"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  getSurrenderCase,
  listSurrenderPayments,
  activateHomeSubscription,
  chargeSurrenderMonth,
  startFacilityTransfer,
  convertToFacility,
  type SurrenderCase,
  type SubscriptionPayment,
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
  formatMoney,
  formatDate,
} from "../../_components/ui";
import {
  surrenderStatusLabels,
  surrenderTypeLabels,
  paymentStatusLabels,
} from "../../_components/labels";

function paymentTone(status: SubscriptionPayment["status"]): "green" | "amber" | "red" | "gray" {
  if (status === "paid") return "green";
  if (status === "pending") return "amber";
  if (status === "failed") return "red";
  return "gray";
}

export default function SurrenderCaseDetail() {
  const token = useAdminToken();
  const params = useParams<{ id: string }>();
  const caseId = Number(params.id);

  const [data, setData] = useState<SurrenderCase | null>(null);
  const [payments, setPayments] = useState<SubscriptionPayment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const [c, p] = await Promise.all([
        getSurrenderCase(token, caseId),
        listSurrenderPayments(token, caseId),
      ]);
      setData(c);
      setPayments(p);
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
        title={`תיק מסירה #${caseId}`}
        action={
          <Link href="/admin/surrender-cases" className="btn-outline text-sm">
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
              <Badge>{surrenderStatusLabels[data.status]}</Badge>
            </div>
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <Field label="סוג מסירה">{surrenderTypeLabels[data.surrender_type]}</Field>
              <Field label="כלב">
                {data.dog_id ? (
                  <Link href={`/admin/dogs/${data.dog_id}`} className="text-brand hover:underline">
                    כלב #{data.dog_id}
                  </Link>
                ) : (
                  "—"
                )}
              </Field>
              <Field label="מוסר (Person ID)">{data.surrenderer_person_id}</Field>
              <Field label="מחיר חודשי">{formatMoney(data.monthly_price)}</Field>
              <Field label="סכום נדרש">{formatMoney(data.total_required_amount)}</Field>
              <Field label="קרדיט מצטבר">{formatMoney(data.accumulated_credit)}</Field>
              <Field label="תאריך התחלה">{formatDate(data.start_date)}</Field>
              <Field label="פרטיות נדרשת">{data.privacy_required ? "כן" : "לא"}</Field>
              <Field label="אישור יצירת קשר ישיר">{data.allow_direct_contact ? "כן" : "לא"}</Field>
              <Field label="סיבת מסירה">{data.reason}</Field>
              <Field label="תאריך פתיחה">{formatDate(data.created_at)}</Field>
            </dl>
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">פעולות</h2>
            <div className="flex flex-wrap gap-2">
              <ActionButton
                onClick={() => runAction(() => activateHomeSubscription(token!, caseId), "מנוי הבית הופעל")}
              >
                הפעלת מנוי בית
              </ActionButton>
              <ActionButton
                variant="outline"
                onClick={() => runAction(() => chargeSurrenderMonth(token!, caseId), "חודש חויב")}
              >
                חיוב חודש
              </ActionButton>
              <ActionButton
                variant="outline"
                onClick={() =>
                  runAction(() => startFacilityTransfer(token!, caseId), "תהליך העברה לפנסיון התחיל")
                }
              >
                התחלת העברה לפנסיון
              </ActionButton>
              <ActionButton
                variant="outline"
                onClick={() => runAction(() => convertToFacility(token!, caseId), "התיק הומר לפנסיון")}
              >
                המרה לפנסיון
              </ActionButton>
            </div>
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">תשלומים</h2>
            {payments.length === 0 ? (
              <p className="text-sm text-gray-500">אין תשלומים רשומים.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-right text-sm">
                  <thead className="border-b bg-gray-50 text-xs text-gray-500">
                    <tr>
                      <th className="px-3 py-2 font-medium">חודש</th>
                      <th className="px-3 py-2 font-medium">סכום</th>
                      <th className="px-3 py-2 font-medium">סטטוס</th>
                      <th className="px-3 py-2 font-medium">תאריך</th>
                      <th className="px-3 py-2 font-medium">אסמכתא</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.map((p) => (
                      <tr key={p.id} className="border-b last:border-0">
                        <td className="px-3 py-2">{p.month_index}</td>
                        <td className="px-3 py-2">{formatMoney(p.amount)}</td>
                        <td className="px-3 py-2">
                          <Badge tone={paymentTone(p.status)}>{paymentStatusLabels[p.status]}</Badge>
                        </td>
                        <td className="px-3 py-2">{formatDate(p.payment_date)}</td>
                        <td className="px-3 py-2 text-gray-500">{p.payment_provider_reference ?? "—"}</td>
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
