"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function AdminLogin() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const f = new FormData(e.currentTarget);
    try {
      const token = await login(String(f.get("email")), String(f.get("password")));
      localStorage.setItem("sadot_token", token);
      router.push("/admin");
    } catch {
      setError("התחברות נכשלה. בדקו אימייל וסיסמה.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card mx-auto max-w-sm space-y-4">
      <h1 className="text-xl font-bold text-brand-dark">כניסת עובדי שדות</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <label className="label">אימייל</label>
          <input name="email" type="email" required className="input" defaultValue="admin@sadot.local" />
        </div>
        <div>
          <label className="label">סיסמה</label>
          <input name="password" type="password" required className="input" />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className="btn-primary w-full disabled:opacity-60">
          {submitting ? "מתחבר..." : "כניסה"}
        </button>
      </form>
    </div>
  );
}
