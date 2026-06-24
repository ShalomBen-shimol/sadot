"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitSurrenderLead } from "@/lib/api";

export default function SurrenderPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const f = new FormData(e.currentTarget);
    try {
      if (!f.get("consent_privacy")) throw new Error("יש לאשר את מדיניות הפרטיות");
      await submitSurrenderLead({
        first_name: f.get("first_name"),
        last_name: f.get("last_name"),
        phone: f.get("phone"),
        city: f.get("city"),
        reason: f.get("reason"),
        surrender_type: f.get("surrender_type"),
        privacy_required: f.get("privacy_required") === "on",
        allow_direct_contact: f.get("allow_direct_contact") === "on",
        consent_privacy: f.get("consent_privacy") === "on",
        dog_name: f.get("dog_name"),
        dog_breed: f.get("dog_breed"),
        dog_age: f.get("dog_age") ? Number(f.get("dog_age")) : null,
        dog_gender: f.get("dog_gender"),
        chip_number: f.get("chip_number"),
        behavior_notes: f.get("behavior_notes"),
      });
      router.push("/thank-you?type=surrender");
    } catch (err) {
      setError(err instanceof Error ? err.message : "אירעה שגיאה");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-brand-dark">מסירת כלב</h1>
        <p className="mt-2 text-gray-600">
          אנחנו יודעים שזו החלטה לא פשוטה. נלווה אתכם ברגישות ובדיסקרטיות לאורך כל הדרך.
        </p>
      </div>

      <form onSubmit={onSubmit} className="card space-y-5">
        <fieldset className="space-y-3">
          <legend className="font-bold text-brand-dark">מסלול מבוקש</legend>
          <select name="surrender_type" className="input" defaultValue="facility">
            <option value="facility">מסירה לפנסיון</option>
            <option value="home_subscription">מסירה מהבית (מנוי חודשי)</option>
            <option value="full">מסירה מלאה</option>
          </select>
        </fieldset>

        <fieldset className="space-y-3">
          <legend className="font-bold text-brand-dark">פרטי המוסר</legend>
          <div className="grid gap-3 sm:grid-cols-2">
            <div><label className="label">שם פרטי *</label><input name="first_name" required className="input" /></div>
            <div><label className="label">שם משפחה</label><input name="last_name" className="input" /></div>
            <div><label className="label">טלפון *</label><input name="phone" required className="input" /></div>
            <div><label className="label">יישוב</label><input name="city" className="input" /></div>
          </div>
          <div><label className="label">סיבת המסירה</label><textarea name="reason" rows={2} className="input" /></div>
        </fieldset>

        <fieldset className="space-y-3">
          <legend className="font-bold text-brand-dark">פרטי הכלב</legend>
          <div className="grid gap-3 sm:grid-cols-2">
            <div><label className="label">שם הכלב</label><input name="dog_name" className="input" /></div>
            <div><label className="label">גזע</label><input name="dog_breed" className="input" /></div>
            <div><label className="label">גיל (שנים)</label><input name="dog_age" type="number" step="0.5" className="input" /></div>
            <div>
              <label className="label">מין</label>
              <select name="dog_gender" className="input" defaultValue="unknown">
                <option value="male">זכר</option>
                <option value="female">נקבה</option>
                <option value="unknown">לא ידוע</option>
              </select>
            </div>
            <div><label className="label">מספר שבב</label><input name="chip_number" className="input" /></div>
          </div>
          <div><label className="label">הערות התנהגות</label><textarea name="behavior_notes" rows={2} className="input" /></div>
        </fieldset>

        <div className="space-y-2 text-sm">
          <label className="flex items-center gap-2"><input type="checkbox" name="privacy_required" /> אבקש טיפול דיסקרטי</label>
          <label className="flex items-center gap-2"><input type="checkbox" name="allow_direct_contact" /> מאשר/ת שמאמצים ייצרו קשר ישיר (במסירה מהבית)</label>
          <label className="flex items-center gap-2"><input type="checkbox" name="consent_privacy" required /> קראתי ואני מאשר/ת את מדיניות הפרטיות *</label>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={submitting} className="btn-primary w-full disabled:opacity-60">
          {submitting ? "שולח..." : "שליחת פנייה"}
        </button>
      </form>
    </div>
  );
}
