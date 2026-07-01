"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getConversation, type ConversationDetail } from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  Badge,
  Field,
  formatDateTime,
} from "../../_components/ui";

export default function ConversationDetailPage() {
  const token = useAdminToken();
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const [data, setData] = useState<ConversationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    getConversation(token, id)
      .then(setData)
      .catch((e) => setError(errorMessage(e)));
  }, [token, id]);

  if (token === undefined || (data === null && !error)) return <Spinner />;

  const conv = data?.conversation;
  const collected = conv?.collected ?? {};

  return (
    <div className="space-y-6">
      <PageHeader
        title={`שיחה #${id}`}
        action={
          <Link href="/admin/conversations" className="btn-outline text-sm">
            חזרה לרשימה
          </Link>
        }
      />
      {error && <ErrorBox message={error} />}

      {data && conv && (
        <>
          <div className="card space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-brand-dark">פרטי השיחה</h2>
              {conv.escalated && <Badge tone="amber">הוסלמה לטיפול אנושי</Badge>}
            </div>
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <Field label="ערוץ">{conv.channel === "whatsapp" ? "WhatsApp" : "אתר"}</Field>
              <Field label="סטטוס">{conv.status}</Field>
              <Field label="מזהה חיצוני">{conv.external_id ?? "—"}</Field>
              <Field label="ליד שנוצר">
                {conv.surrender_case_id ? (
                  <Link
                    href={`/admin/surrender-cases/${conv.surrender_case_id}`}
                    className="text-brand hover:underline"
                  >
                    תיק מסירה #{conv.surrender_case_id}
                  </Link>
                ) : (
                  "—"
                )}
              </Field>
              <Field label="עודכן">{formatDateTime(conv.updated_at)}</Field>
            </dl>
            {Object.keys(collected).length > 0 && (
              <div>
                <p className="mb-1 text-xs font-medium text-gray-500">פרטים שנאספו</p>
                <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
                  {Object.entries(collected).map(([k, v]) => (
                    <div key={k}>
                      <dt className="text-xs text-gray-400">{k}</dt>
                      <dd className="text-gray-900">{String(v)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
          </div>

          <div className="card space-y-3">
            <h2 className="text-lg font-semibold text-brand-dark">תמליל</h2>
            <div className="space-y-3">
              {data.messages.map((m) => (
                <div key={m.id} className={`flex ${m.role === "user" ? "justify-start" : "justify-end"}`}>
                  <div
                    className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
                      m.role === "user"
                        ? "bg-brand text-white"
                        : "border border-gray-200 bg-gray-50 text-gray-800"
                    }`}
                  >
                    {m.content}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
