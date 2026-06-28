"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { listAdoptionCases, type AdoptionCase, type AdoptionStatus } from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  Badge,
  formatDate,
} from "../_components/ui";
import { adoptionStatusLabels } from "../_components/labels";

const STATUS_OPTIONS = Object.entries(adoptionStatusLabels) as [AdoptionStatus, string][];

export default function AdoptionCasesPage() {
  const token = useAdminToken();
  const [cases, setCases] = useState<AdoptionCase[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<AdoptionStatus | "">("");

  const load = useCallback(() => {
    if (!token) return;
    setCases(null);
    listAdoptionCases(token, status ? { status } : {})
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
      <PageHeader title="תיקי אימוץ" subtitle="ניהול תהליכי אימוץ מסינון ועד השלמה" />

      <div className="flex flex-wrap items-center gap-2">
        <label className="text-sm text-gray-600">סינון לפי סטטוס:</label>
        <select
          className="input max-w-xs"
          value={status}
          onChange={(e) => setStatus(e.target.value as AdoptionStatus | "")}
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
                <th className="px-4 py-3 font-medium">כלב</th>
                <th className="px-4 py-3 font-medium">מאמץ</th>
                <th className="px-4 py-3 font-medium">סטטוס</th>
                <th className="px-4 py-3 font-medium">אימוץ ביתי ישיר</th>
                <th className="px-4 py-3 font-medium">פגישה</th>
                <th className="px-4 py-3 font-medium">תאריך פתיחה</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/admin/adoption-cases/${c.id}`} className="font-medium text-brand hover:underline">
                      {c.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">כלב #{c.dog_id}</td>
                  <td className="px-4 py-3">Person #{c.adopter_person_id}</td>
                  <td className="px-4 py-3">
                    <Badge>{adoptionStatusLabels[c.status]}</Badge>
                  </td>
                  <td className="px-4 py-3">{c.is_direct_home_adoption ? "כן" : "לא"}</td>
                  <td className="px-4 py-3">{formatDate(c.meeting_date)}</td>
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
