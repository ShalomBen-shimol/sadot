"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getDashboardSummary, type DashboardSummary } from "@/lib/api";
import { useAdminToken, errorMessage, ErrorBox, Spinner, PageHeader } from "./_components/ui";

type Card = { key: keyof DashboardSummary; label: string; href: string };

const CARDS: Card[] = [
  { key: "adoption_leads", label: "לידים חדשים לאימוץ", href: "/admin/adoption-cases" },
  { key: "dogs_available", label: "כלבים זמינים לאימוץ", href: "/admin/dogs" },
  { key: "transfers_awaiting_authority", label: "העברות פתוחות (ממתינות לרשות)", href: "/admin/ownership-transfers" },
  { key: "surrender_cases", label: "תיקי מסירה", href: "/admin/surrender-cases" },
  { key: "open_tasks", label: "משימות פתוחות", href: "/admin" },
  { key: "dogs_in_facility", label: "כלבים בפנסיון", href: "/admin/dogs" },
  { key: "adoption_cases", label: "תיקי אימוץ", href: "/admin/adoption-cases" },
  { key: "dogs_adopted", label: "אומצו", href: "/admin/dogs" },
];

export default function AdminDashboard() {
  const token = useAdminToken();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    getDashboardSummary(token)
      .then((s) => {
        setSummary(s);
        setError(null);
      })
      .catch((e) => setError(errorMessage(e)));
  }, [token]);

  return (
    <div className="space-y-6">
      <PageHeader title="לוח בקרה" subtitle="סיכום פעילות הפנסיון" />

      {error && <ErrorBox message={error} />}

      {!summary && !error && <Spinner />}

      {summary && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {CARDS.map((c) => (
            <Link key={c.label} href={c.href} className="card text-center transition hover:shadow-md">
              <div className="text-3xl font-bold text-brand">{summary[c.key]}</div>
              <div className="mt-1 text-sm text-gray-600">{c.label}</div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
