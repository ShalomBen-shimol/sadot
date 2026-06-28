"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  listOwnershipTransfers,
  runTransferFollowups,
  type OwnershipTransfer,
} from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  Badge,
  ActionButton,
  formatDate,
} from "../_components/ui";
import { ownershipTransferStatusLabels, transferTypeLabels } from "../_components/labels";

export default function OwnershipTransfersPage() {
  const token = useAdminToken();
  const [transfers, setTransfers] = useState<OwnershipTransfer[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    setTransfers(null);
    listOwnershipTransfers(token)
      .then((t) => {
        setTransfers(t);
        setError(null);
      })
      .catch((e) => setError(errorMessage(e)));
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  async function runFollowups() {
    if (!token) return;
    setNotice(null);
    setError(null);
    try {
      const res = await runTransferFollowups(token);
      setNotice(`${res.detail} (${res.reminders_created} תזכורות נוצרו)`);
      load();
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="העברות בעלות"
        subtitle="מעקב אחר העברות מול הרשויות"
        action={
          <ActionButton variant="outline" onClick={runFollowups}>
            הרצת מעקבים
          </ActionButton>
        }
      />

      {error && <ErrorBox message={error} />}
      {notice && <div className="card border-green-200 bg-green-50 text-sm text-green-700">{notice}</div>}
      {!transfers && !error && <Spinner />}

      {transfers && transfers.length === 0 && (
        <div className="card text-sm text-gray-500">לא נמצאו העברות.</div>
      )}

      {transfers && transfers.length > 0 && (
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-right text-sm">
            <thead className="border-b bg-gray-50 text-xs text-gray-500">
              <tr>
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">כלב</th>
                <th className="px-4 py-3 font-medium">סוג</th>
                <th className="px-4 py-3 font-medium">סטטוס</th>
                <th className="px-4 py-3 font-medium">נשלח לרשות</th>
                <th className="px-4 py-3 font-medium">מעקב הבא</th>
              </tr>
            </thead>
            <tbody>
              {transfers.map((t) => (
                <tr key={t.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/admin/ownership-transfers/${t.id}`} className="font-medium text-brand hover:underline">
                      {t.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/admin/dogs/${t.dog_id}`} className="text-brand hover:underline">
                      כלב #{t.dog_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{transferTypeLabels[t.transfer_type]}</td>
                  <td className="px-4 py-3">
                    <Badge>{ownershipTransferStatusLabels[t.status]}</Badge>
                  </td>
                  <td className="px-4 py-3">{formatDate(t.sent_to_authority_at)}</td>
                  <td className="px-4 py-3">{formatDate(t.next_followup_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
