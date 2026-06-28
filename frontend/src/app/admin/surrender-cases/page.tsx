"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { listSurrenderCases, type SurrenderCase, type SurrenderStatus } from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  Badge,
  formatMoney,
  formatDate,
} from "../_components/ui";
import { surrenderStatusLabels, surrenderTypeLabels } from "../_components/labels";

const STATUS_OPTIONS = Object.entries(surrenderStatusLabels) as [SurrenderStatus, string][];

export default function SurrenderCasesPage() {
  const token = useAdminToken();
  const [cases, setCases] = useState<SurrenderCase[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<SurrenderStatus | "">("");

  const load = useCallback(() => {
    if (!token) return;
    setCases(null);
    listSurrenderCases(token, status ? { status } : {})
      .then((c) => {
        setCases(c);
        setError(null);
      })
      .catch((e) => setError(errorMessage(e)));
  }, [token, status]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      <PageHeader title="תיקי מסירה" subtitle="ניהול מסירות, מנויי בית והעברה לפנסיון" />

      <div className="flex flex-wrap items-center gap-2">
        <label className="text-sm text-gray-600">סינון לפי סטטוס:</label>
        <select
          className="input max-w-xs"
          value={status}
          onChange={(e) => setStatus(e.target.value as SurrenderStatus | "")}
        >
          <option value="">הכל</option>
          {STATUS_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {error && <ErrorBox message={error} />}
      {!cases && !error && <Spinner />}

      {cases && cases.length === 0 && <div className="card text-sm text-gray-500">לא נמצאו תיקים.</div>}

      {cases && cases.length > 0 && (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-right text-sm">
            <thead className="border-b bg-gray-50 text-xs text-gray-500">
              <tr>
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">סוג</th>
                <th className="px-4 py-3 font-medium">סטטוס</th>
                <th className="px-4 py-3 font-medium">מחיר חודשי</th>
                <th className="px-4 py-3 font-medium">קרדיט מצטבר</th>
                <th className="px-4 py-3 font-medium">תאריך פתיחה</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/admin/surrender-cases/${c.id}`} className="font-medium text-brand hover:underline">
                      {c.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{surrenderTypeLabels[c.surrender_type]}</td>
                  <td className="px-4 py-3">
                    <Badge>{surrenderStatusLabels[c.status]}</Badge>
                  </td>
                  <td className="px-4 py-3">{formatMoney(c.monthly_price)}</td>
                  <td className="px-4 py-3">{formatMoney(c.accumulated_credit)}</td>
                  <td className="px-4 py-3">{formatDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
