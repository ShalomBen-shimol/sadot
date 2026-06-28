"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const TOKEN_KEY = "sadot_token";

// Reads the stored admin token on the client. While the value is undefined the
// component is still hydrating; null means "no token -> redirect to login".
export function useAdminToken(): string | undefined {
  const router = useRouter();
  const [token, setToken] = useState<string | undefined>(undefined);

  useEffect(() => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) {
      router.replace("/admin/login");
      return;
    }
    setToken(t);
  }, [router]);

  return token;
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// Extracts a human-readable message from an API error (the client throws Error
// with the raw response body, which is usually JSON like {"detail": "..."}).
export function errorMessage(err: unknown): string {
  if (err instanceof Error) {
    try {
      const parsed = JSON.parse(err.message);
      if (parsed && typeof parsed.detail === "string") return parsed.detail;
    } catch {
      /* not JSON */
    }
    return err.message || "אירעה שגיאה";
  }
  return "אירעה שגיאה";
}

export function Spinner() {
  return <div className="py-8 text-center text-sm text-gray-500">טוען...</div>;
}

export function ErrorBox({ message }: { message: string }) {
  return <div className="card border-red-200 bg-red-50 text-sm text-red-700">{message}</div>;
}

export function Badge({ children, tone = "brand" }: { children: React.ReactNode; tone?: "brand" | "green" | "amber" | "red" | "gray" }) {
  const tones: Record<string, string> = {
    brand: "bg-brand-light text-brand-dark",
    green: "bg-green-100 text-green-800",
    amber: "bg-amber-100 text-amber-800",
    red: "bg-red-100 text-red-800",
    gray: "bg-gray-100 text-gray-700",
  };
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-brand-dark">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

// Action button that runs an async handler, shows a busy state and disables
// itself while pending. Used for status-transition / workflow actions.
export function ActionButton({
  onClick,
  children,
  variant = "primary",
  disabled,
}: {
  onClick: () => Promise<void> | void;
  children: React.ReactNode;
  variant?: "primary" | "outline" | "danger";
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  async function handle() {
    if (busy || disabled) return;
    setBusy(true);
    try {
      await onClick();
    } finally {
      setBusy(false);
    }
  }
  const cls =
    variant === "primary"
      ? "btn-primary"
      : variant === "danger"
        ? "btn border border-red-300 text-red-700 hover:bg-red-50"
        : "btn-outline";
  return (
    <button onClick={handle} disabled={busy || disabled} className={`${cls} text-sm disabled:opacity-50`}>
      {busy ? "..." : children}
    </button>
  );
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("he-IL", { year: "numeric", month: "2-digit", day: "2-digit" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("he-IL", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value.toLocaleString("he-IL")} ₪`;
}

// Small label/value pair for case-file detail grids.
export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-gray-500">{label}</dt>
      <dd className="mt-0.5 text-sm text-gray-900">{children ?? "—"}</dd>
    </div>
  );
}
