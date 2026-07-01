"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listConversations, type ConversationRow } from "@/lib/api";
import { useAdminToken, errorMessage, ErrorBox, Spinner, PageHeader, Badge, formatDateTime } from "../_components/ui";

const STATUS: Record<ConversationRow["status"], { label: string; tone: "brand" | "green" | "amber" | "gray" }> = {
  active: { label: "פעילה", tone: "brand" },
  lead_created: { label: "נוצר ליד", tone: "green" },
  escalated: { label: "הוסלמה", tone: "amber" },
  closed: { label: "נסגרה", tone: "gray" },
};

export default function ConversationsPage() {
  const token = useAdminToken();
  const [rows, setRows] = useState<ConversationRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    listConversations(token)
      .then(setRows)
      .catch((e) => setError(errorMessage(e)));
  }, [token]);

  if (token === undefined || (rows === null && !error)) return <Spinner />;

  return (
    <div className="space-y-6">
      <PageHeader title="שיחות צ'אט" subtitle="שיחות מבקרים עם הבוט" />
      {error && <ErrorBox message={error} />}
      {rows && (
        <div className="card overflow-x-auto p-0">
          <table className="min-w-full text-right text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500">
              <tr>
                <th className="px-3 py-2 font-medium">#</th>
                <th className="px-3 py-2 font-medium">ערוץ</th>
                <th className="px-3 py-2 font-medium">סטטוס</th>
                <th className="px-3 py-2 font-medium">הוסלמה</th>
                <th className="px-3 py-2 font-medium">עודכן</th>
                <th className="px-3 py-2 font-medium"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((c) => (
                <tr key={c.id} className={c.escalated ? "bg-amber-50/50" : "hover:bg-gray-50"}>
                  <td className="px-3 py-2 font-medium text-gray-900">{c.id}</td>
                  <td className="px-3 py-2 text-gray-600">{c.channel === "whatsapp" ? "WhatsApp" : "אתר"}</td>
                  <td className="px-3 py-2">
                    <Badge tone={STATUS[c.status].tone}>{STATUS[c.status].label}</Badge>
                  </td>
                  <td className="px-3 py-2">{c.escalated ? "⚠️" : "—"}</td>
                  <td className="px-3 py-2 text-gray-500">{formatDateTime(c.updated_at)}</td>
                  <td className="px-3 py-2">
                    <Link href={`/admin/conversations/${c.id}`} className="text-brand-dark hover:underline">
                      צפייה
                    </Link>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-gray-400">
                    אין שיחות עדיין.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
