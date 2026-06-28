"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import ConsentNotice from "@/components/ConsentNotice";
import DocumentUpload from "@/components/DocumentUpload";
import { submitAdoptionLead } from "@/lib/api";

// Adoption interest form. Used from a dog page (pass `dogId`) or standalone for a
// general "looking to adopt" lead. Collects adopter-matching info + consents and
// calls submitAdoptionLead.

type FormState = {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  city: string;
  home_type: string;
  experience_level: string;
  hours_alone: string;
  has_children: boolean;
  has_other_dogs: boolean;
  notes: string;
  consent_messages: boolean;
  consent_privacy: boolean;
};

const INITIAL: FormState = {
  first_name: "",
  last_name: "",
  phone: "",
  email: "",
  city: "",
  home_type: "apartment",
  experience_level: "none",
  hours_alone: "",
  has_children: false,
  has_other_dogs: false,
  notes: "",
  consent_messages: false,
  consent_privacy: false,
};

function isValidPhone(raw: string): boolean {
  const digits = raw.replace(/\D/g, "");
  return /^0\d{8,9}$/.test(digits);
}

export default function AdoptionForm({ dogId }: { dogId?: number }) {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(INITIAL);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!form.first_name.trim()) {
      setError("נא למלא שם פרטי");
      return;
    }
    if (!isValidPhone(form.phone)) {
      setError("מספר הטלפון אינו תקין");
      return;
    }
    if (!form.consent_privacy) {
      setError("יש לאשר את הודעת הפרטיות כדי לשלוח");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitAdoptionLead({
        dog_id: dogId ?? null,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim() || null,
        phone: form.phone.trim(),
        email: form.email.trim() || null,
        city: form.city.trim() || null,
        home_type: form.home_type,
        experience_level: form.experience_level,
        hours_alone: form.hours_alone.trim() || null,
        has_children: form.has_children,
        has_other_dogs: form.has_other_dogs,
        consent_messages: form.consent_messages,
        consent_privacy: form.consent_privacy,
        source: "website",
        notes: form.notes.trim() || null,
      });
      router.push("/thank-you?type=adoption");
    } catch (err) {
      setError(err instanceof Error ? err.message : "אירעה שגיאה, נסו שוב");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="card space-y-5">
      <h3 className="text-lg font-bold text-brand-dark">השארת פנייה לאימוץ</h3>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="label">שם פרטי *</label>
          <input
            className="input py-3 text-base"
            value={form.first_name}
            onChange={(e) => set("first_name", e.target.value)}
            autoComplete="given-name"
          />
        </div>
        <div>
          <label className="label">שם משפחה</label>
          <input
            className="input py-3 text-base"
            value={form.last_name}
            onChange={(e) => set("last_name", e.target.value)}
            autoComplete="family-name"
          />
        </div>
        <div>
          <label className="label">טלפון *</label>
          <input
            className="input py-3 text-base"
            type="tel"
            inputMode="tel"
            value={form.phone}
            onChange={(e) => set("phone", e.target.value)}
            autoComplete="tel"
            placeholder="050-0000000"
          />
        </div>
        <div>
          <label className="label">אימייל</label>
          <input
            className="input py-3 text-base"
            type="email"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
            autoComplete="email"
          />
        </div>
        <div>
          <label className="label">יישוב</label>
          <input
            className="input py-3 text-base"
            value={form.city}
            onChange={(e) => set("city", e.target.value)}
            autoComplete="address-level2"
          />
        </div>
        <div>
          <label className="label">סוג מגורים</label>
          <select
            className="input py-3 text-base"
            value={form.home_type}
            onChange={(e) => set("home_type", e.target.value)}
          >
            <option value="apartment">דירה</option>
            <option value="house">בית פרטי</option>
            <option value="house_with_yard">בית עם חצר</option>
          </select>
        </div>
        <div>
          <label className="label">ניסיון עם כלבים</label>
          <select
            className="input py-3 text-base"
            value={form.experience_level}
            onChange={(e) => set("experience_level", e.target.value)}
          >
            <option value="none">ללא ניסיון</option>
            <option value="some">מעט ניסיון</option>
            <option value="experienced">מנוסה</option>
          </select>
        </div>
        <div>
          <label className="label">כמה שעות הכלב יישאר לבד?</label>
          <input
            className="input py-3 text-base"
            value={form.hours_alone}
            onChange={(e) => set("hours_alone", e.target.value)}
            placeholder="לדוגמה: 4-6 שעות"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="h-5 w-5"
            checked={form.has_children}
            onChange={(e) => set("has_children", e.target.checked)}
          />
          יש ילדים בבית
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="h-5 w-5"
            checked={form.has_other_dogs}
            onChange={(e) => set("has_other_dogs", e.target.checked)}
          />
          יש כלבים נוספים
        </label>
      </div>

      <div>
        <label className="label">הערות</label>
        <textarea
          className="input"
          rows={3}
          value={form.notes}
          onChange={(e) => set("notes", e.target.value)}
        />
      </div>

      <ConsentNotice variant="adoption" />

      <div className="space-y-3 text-sm">
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-5 w-5"
            checked={form.consent_messages}
            onChange={(e) => set("consent_messages", e.target.checked)}
          />
          <span>אני מאשר/ת קבלת הודעות עדכון בנוגע לאימוץ</span>
        </label>
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-1 h-5 w-5"
            checked={form.consent_privacy}
            onChange={(e) => set("consent_privacy", e.target.checked)}
          />
          <span>קראתי ואני מאשר/ת את הודעת הפרטיות *</span>
        </label>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-semibold text-brand-dark">
          מסמכים (לא חובה כעת)
        </p>
        <DocumentUpload
          label="תמונה שלכם עם הכלב / בבית"
          documentType="adopter_with_dog_photo"
          hint="עוזר לנו להכיר אתכם ולוודא התאמה. נבקש זאת גם בהמשך התהליך."
        />
      </div>

      {error && <p className="text-sm font-medium text-red-600">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="btn-primary w-full py-3 text-base disabled:opacity-60"
      >
        {submitting ? "שולח…" : "שליחת פנייה"}
      </button>
    </form>
  );
}
