"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authGet } from "@/lib/api";

type Summary = {
  dogs_total: number;
  dogs_available: number;
  dogs_in_facility: number;
  dogs_adopted: number;
  surrender_cases: number;
  adoption_leads: number;
  adoption_cases: number;
  open_tasks: number;
  transfers_awaiting_authority: number;
};

const CARDS: { key: keyof Summary; label: string }[] = [
  { key: "dogs_available", label: "כלבים זמינים לאימוץ" },
  { key: "dogs_in_facility", label: "כלבים בפנסיון" },
  { key: "dogs_adopted", label: "אומצו" },
  { key: "surrender_cases", label: "תיקי מסירה" },
  { key: "adoption_leads", label: "לידים לאימוץ" },
  { key: "adoption_cases", label: "תיקי אימוץ" },
  { key: "open_tasks", label: "משימות פתוחות" },
  { key: "transfers_awaiting_authority", label: "ממתינים לאישור רשות" },
];

export default function AdminDashboard() {
  const router = useRouter();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("sadot_token");
    if (!token) {
      router.push("/admin/login");
      return;
    }
    authGet<Summary>("/api/v1/dashboard/summary", token)
      .then(setSummary)
      .catch(() => {
        setError("פג תוקף ההתחברות. אנא התחברו מחדש.");
        localStorage.removeItem("sadot_token");
      });
  }, [router]);

  function logout() {
    localStorage.removeItem("sadot_token");
    router.push("/admin/login");
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-brand-dark">לוח בקרה</h1>
        <button onClick={logout} className="text-sm text-gray-500 hover:text-brand">התנתקות</button>
      </div>

      {error && (
        <div className="card text-red-600">
          {error} <Link href="/admin/login" className="underline">להתחברות</Link>
        </div>
      )}

      {summary && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {CARDS.map((c) => (
            <div key={c.key} className="card text-center">
              <div className="text-3xl font-bold text-brand">{summary[c.key]}</div>
              <div className="mt-1 text-sm text-gray-600">{c.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="card text-sm text-gray-600">
        זהו לוח הבקרה הבסיסי של שלב 1. ניהול מלא של כלבים, תיקים, משימות ופייפליין
        סטטוסים זמין דרך ה-API (ראו <code className="rounded bg-gray-100 px-1">/docs</code>).
      </div>
    </div>
  );
}
