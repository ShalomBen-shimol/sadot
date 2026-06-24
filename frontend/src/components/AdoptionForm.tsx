"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitAdoptionLead } from "@/lib/api";

export default function AdoptionForm({ dogId }: { dogId?: number }) {
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
      await submitAdoptionLead({
        dog_id: dogId,
        first_name: f.get("first_name"),
        last_name: f.get("last_name"),
        phone: f.get("phone"),
        email: f.get("email") || null,
        city: f.get("city"),
        home_type: f.get("home_type"),
        experience_level: f.get("experience_level"),
        has_children: f.get("has_children") === "on",
        has_other_dogs: f.get("has_other_dogs") === "on",
        hours_alone: f.get("hours_alone"),
        consent_messages: f.get("consent_messages") === "on",
        consent_privacy: f.get("consent_privacy") === "on",
        source: "website",
        notes: f.get("notes"),
      });
      router.push("/thank-you?type=adoption");
    } catch (err) {
      setError(err instanceof Error ? err.message : "אירעה שגיאה");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="card space-y-4">
      <h3 className="text-lg font-bold text-brand-dark">השארת פנייה לאימוץ</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="label">שם פרטי *</label>
          <input name="first_name" required className="input" />
        </div>
        <div>
          <label className="label">שם משפחה</label>
          <input name="last_name" className="input" />
        </div>
        <div>
          <label className="label">טלפון *</label>
          <input name="phone" required className="input" />
        </div>
        <div>
          <label className="label">אימייל</label>
          <input name="email" type="email" className="input" />
        </div>
        <div>
          <label className="label">יישוב</label>
          <input name="city" className="input" />
        </div>
        <div>
          <label className="label">סוג בית</label>
          <select name="home_type" className="input">
            <option value="apartment">דירה</option>
            <option value="house">בית פרטי</option>
          </select>
        </div>
        <div>
          <label className="label">ניסיון עם כלבים</label>
          <select name="experience_level" className="input">
            <option value="none">ללא ניסיון</option>
            <option value="some">מעט ניסיון</option>
            <option value="experienced">מנוסה</option>
          </select>
        </div>
        <div>
          <label className="label">כמה שעות הכלב יישאר לבד?</label>
          <input name="hours_alone" className="input" placeholder="לדוגמה: 4-6 שעות" />
        </div>
      </div>

      <div className="flex flex-wrap gap-4 text-sm">
        <label className="flex items-center gap-2"><input type="checkbox" name="has_children" /> יש ילדים בבית</label>
        <label className="flex items-center gap-2"><input type="checkbox" name="has_other_dogs" /> יש כלבים נוספים</label>
      </div>

      <div>
        <label className="label">הערות</label>
        <textarea name="notes" className="input" rows={3} />
      </div>

      <div className="space-y-2 text-sm">
        <label className="flex items-center gap-2">
          <input type="checkbox" name="consent_messages" /> אני מאשר/ת קבלת הודעות
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" name="consent_privacy" required /> קראתי ואני מאשר/ת את מדיניות הפרטיות *
        </label>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      <button type="submit" disabled={submitting} className="btn-primary w-full disabled:opacity-60">
        {submitting ? "שולח..." : "שליחת פנייה"}
      </button>
    </form>
  );
}
