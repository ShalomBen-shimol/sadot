"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { listDogs, type Dog, type DogStatus } from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  Badge,
  formatDate,
} from "../_components/ui";
import { dogStatusLabels, dogGenderLabels, locationTypeLabels } from "../_components/labels";

const STATUS_OPTIONS = Object.entries(dogStatusLabels) as [DogStatus, string][];

export default function DogsPage() {
  const token = useAdminToken();
  const [dogs, setDogs] = useState<Dog[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<DogStatus | "">("");

  const load = useCallback(() => {
    if (!token) return;
    setDogs(null);
    listDogs(token, status ? { status } : {})
      .then((d) => {
        setDogs(d);
        setError(null);
      })
      .catch((e) => setError(errorMessage(e)));
  }, [token, status]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      <PageHeader title="כלבים" subtitle="ניהול תיקי הכלבים בפנסיון" />

      <div className="flex flex-wrap items-center gap-2">
        <label className="text-sm text-gray-600">סינון לפי סטטוס:</label>
        <select
          className="input max-w-xs"
          value={status}
          onChange={(e) => setStatus(e.target.value as DogStatus | "")}
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
      {!dogs && !error && <Spinner />}

      {dogs && dogs.length === 0 && <div className="card text-sm text-gray-500">לא נמצאו כלבים.</div>}

      {dogs && dogs.length > 0 && (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-right text-sm">
            <thead className="border-b bg-gray-50 text-xs text-gray-500">
              <tr>
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">שם</th>
                <th className="px-4 py-3 font-medium">גזע</th>
                <th className="px-4 py-3 font-medium">מין</th>
                <th className="px-4 py-3 font-medium">מיקום</th>
                <th className="px-4 py-3 font-medium">סטטוס</th>
                <th className="px-4 py-3 font-medium">נוצר</th>
              </tr>
            </thead>
            <tbody>
              {dogs.map((d) => (
                <tr key={d.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/admin/dogs/${d.id}`} className="font-medium text-brand hover:underline">
                      {d.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{d.name ?? "—"}</td>
                  <td className="px-4 py-3">{d.breed ?? "—"}</td>
                  <td className="px-4 py-3">{dogGenderLabels[d.gender]}</td>
                  <td className="px-4 py-3">{locationTypeLabels[d.current_location_type]}</td>
                  <td className="px-4 py-3">
                    <Badge>{dogStatusLabels[d.status]}</Badge>
                  </td>
                  <td className="px-4 py-3">{formatDate(d.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
