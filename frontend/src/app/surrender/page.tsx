"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import ConsentNotice from "@/components/ConsentNotice";
import DocumentUpload from "@/components/DocumentUpload";
import {
  submitSurrenderLead,
  type DogGender,
  type DogSize,
  type SurrenderType,
} from "@/lib/api";

// Tri-state helper: "" => unknown/null, "yes"/"no" => boolean.
type Tri = "" | "yes" | "no";
const triToBool = (v: Tri): boolean | null =>
  v === "" ? null : v === "yes";

type FormState = {
  // surrenderer
  first_name: string;
  last_name: string;
  phone: string;
  city: string;
  // dog
  dog_name: string;
  dog_breed: string;
  dog_age: string;
  dog_gender: DogGender;
  dog_size: "" | DogSize;
  chip_number: string;
  is_neutered: Tri;
  is_vaccinated: Tri;
  good_with_children: Tri;
  good_with_dogs: Tri;
  medical_notes: string;
  behavior_notes: string;
  reason: string;
  // track
  surrender_type: SurrenderType;
  // consent
  privacy_required: boolean;
  allow_direct_contact: boolean;
  consent_privacy: boolean;
};

const INITIAL: FormState = {
  first_name: "",
  last_name: "",
  phone: "",
  city: "",
  dog_name: "",
  dog_breed: "",
  dog_age: "",
  dog_gender: "unknown",
  dog_size: "",
  chip_number: "",
  is_neutered: "",
  is_vaccinated: "",
  good_with_children: "",
  good_with_dogs: "",
  medical_notes: "",
  behavior_notes: "",
  reason: "",
  surrender_type: "facility",
  privacy_required: false,
  allow_direct_contact: false,
  consent_privacy: false,
};

const STEPS = ["פרטי המוסר", "פרטי הכלב", "מסלול המסירה", "אישור ושליחה"];

// Loose Israeli mobile/phone validation (digits only, 9–10 long, starts with 0).
function isValidPhone(raw: string): boolean {
  const digits = raw.replace(/\D/g, "");
  return /^0\d{8,9}$/.test(digits);
}

export default function SurrenderPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(INITIAL);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function validateStep(s: number): string | null {
    if (s === 0) {
      if (!form.first_name.trim()) return "נא למלא שם פרטי";
      if (!form.phone.trim()) return "נא למלא מספר טלפון";
      if (!isValidPhone(form.phone)) return "מספר הטלפון אינו תקין";
    }
    if (s === 3 && !form.consent_privacy) {
      return "יש לאשר את הודעת הפרטיות כדי לשלוח";
    }
    return null;
  }

  function next() {
    const err = validateStep(step);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function back() {
    setError(null);
    setStep((s) => Math.max(s - 1, 0));
  }

  async function onSubmit() {
    const err = validateStep(3);
    if (err) {
      setError(err);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitSurrenderLead({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim() || null,
        phone: form.phone.trim(),
        city: form.city.trim() || null,
        reason: form.reason.trim() || null,
        surrender_type: form.surrender_type,
        privacy_required: form.privacy_required,
        allow_direct_contact: form.allow_direct_contact,
        consent_privacy: form.consent_privacy,
        dog_name: form.dog_name.trim() || null,
        dog_breed: form.dog_breed.trim() || null,
        dog_age: form.dog_age ? Number(form.dog_age) : null,
        dog_gender: form.dog_gender,
        dog_size: form.dog_size || null,
        chip_number: form.chip_number.trim() || null,
        is_neutered: triToBool(form.is_neutered),
        is_vaccinated: triToBool(form.is_vaccinated),
        good_with_children: triToBool(form.good_with_children),
        good_with_dogs: triToBool(form.good_with_dogs),
        medical_notes: form.medical_notes.trim() || null,
        behavior_notes: form.behavior_notes.trim() || null,
      });
      router.push("/thank-you?type=surrender");
    } catch (e) {
      setError(e instanceof Error ? e.message : "אירעה שגיאה, נסו שוב");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-brand-dark">מסירת כלב</h1>
        <p className="mt-2 text-gray-600">
          אנחנו יודעים שזו החלטה לא פשוטה. נלווה אתכם ברגישות ובדיסקרטיות לאורך כל
          הדרך.
        </p>
      </div>

      {/* Step indicator */}
      <ol className="flex items-center gap-2">
        {STEPS.map((label, i) => (
          <li key={label} className="flex flex-1 flex-col items-center gap-1">
            <span
              className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold ${
                i < step
                  ? "bg-brand text-white"
                  : i === step
                  ? "bg-brand text-white ring-4 ring-brand-light"
                  : "bg-gray-200 text-gray-500"
              }`}
            >
              {i + 1}
            </span>
            <span
              className={`text-center text-[11px] leading-tight ${
                i === step ? "font-semibold text-brand-dark" : "text-gray-500"
              }`}
            >
              {label}
            </span>
          </li>
        ))}
      </ol>

      <div className="card space-y-5">
        {step === 0 && (
          <fieldset className="space-y-4">
            <legend className="font-bold text-brand-dark">פרטי המוסר</legend>
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
                <label className="label">יישוב</label>
                <input
                  className="input py-3 text-base"
                  value={form.city}
                  onChange={(e) => set("city", e.target.value)}
                  autoComplete="address-level2"
                />
              </div>
            </div>
          </fieldset>
        )}

        {step === 1 && (
          <fieldset className="space-y-4">
            <legend className="font-bold text-brand-dark">פרטי הכלב</legend>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">שם הכלב</label>
                <input
                  className="input py-3 text-base"
                  value={form.dog_name}
                  onChange={(e) => set("dog_name", e.target.value)}
                />
              </div>
              <div>
                <label className="label">גזע</label>
                <input
                  className="input py-3 text-base"
                  value={form.dog_breed}
                  onChange={(e) => set("dog_breed", e.target.value)}
                />
              </div>
              <div>
                <label className="label">גיל (שנים)</label>
                <input
                  className="input py-3 text-base"
                  type="number"
                  inputMode="decimal"
                  step="0.5"
                  min="0"
                  value={form.dog_age}
                  onChange={(e) => set("dog_age", e.target.value)}
                />
              </div>
              <div>
                <label className="label">מין</label>
                <select
                  className="input py-3 text-base"
                  value={form.dog_gender}
                  onChange={(e) => set("dog_gender", e.target.value as DogGender)}
                >
                  <option value="male">זכר</option>
                  <option value="female">נקבה</option>
                  <option value="unknown">לא ידוע</option>
                </select>
              </div>
              <div>
                <label className="label">גודל</label>
                <select
                  className="input py-3 text-base"
                  value={form.dog_size}
                  onChange={(e) =>
                    set("dog_size", e.target.value as "" | DogSize)
                  }
                >
                  <option value="">לא ידוע</option>
                  <option value="small">קטן</option>
                  <option value="medium">בינוני</option>
                  <option value="large">גדול</option>
                  <option value="xlarge">גדול מאוד</option>
                </select>
              </div>
              <div>
                <label className="label">מספר שבב</label>
                <input
                  className="input py-3 text-base"
                  inputMode="numeric"
                  value={form.chip_number}
                  onChange={(e) => set("chip_number", e.target.value)}
                />
              </div>
              <div>
                <label className="label">מעוקר/ת?</label>
                <select
                  className="input py-3 text-base"
                  value={form.is_neutered}
                  onChange={(e) => set("is_neutered", e.target.value as Tri)}
                >
                  <option value="">לא ידוע</option>
                  <option value="yes">כן</option>
                  <option value="no">לא</option>
                </select>
              </div>
              <div>
                <label className="label">מחוסן/ת?</label>
                <select
                  className="input py-3 text-base"
                  value={form.is_vaccinated}
                  onChange={(e) => set("is_vaccinated", e.target.value as Tri)}
                >
                  <option value="">לא ידוע</option>
                  <option value="yes">כן</option>
                  <option value="no">לא</option>
                </select>
              </div>
              <div>
                <label className="label">מסתדר עם ילדים?</label>
                <select
                  className="input py-3 text-base"
                  value={form.good_with_children}
                  onChange={(e) =>
                    set("good_with_children", e.target.value as Tri)
                  }
                >
                  <option value="">לא ידוע</option>
                  <option value="yes">כן</option>
                  <option value="no">לא</option>
                </select>
              </div>
              <div>
                <label className="label">מסתדר עם כלבים?</label>
                <select
                  className="input py-3 text-base"
                  value={form.good_with_dogs}
                  onChange={(e) => set("good_with_dogs", e.target.value as Tri)}
                >
                  <option value="">לא ידוע</option>
                  <option value="yes">כן</option>
                  <option value="no">לא</option>
                </select>
              </div>
            </div>
            <div>
              <label className="label">הערות רפואיות</label>
              <textarea
                className="input"
                rows={2}
                value={form.medical_notes}
                onChange={(e) => set("medical_notes", e.target.value)}
              />
            </div>
            <div>
              <label className="label">הערות התנהגות</label>
              <textarea
                className="input"
                rows={2}
                value={form.behavior_notes}
                onChange={(e) => set("behavior_notes", e.target.value)}
              />
            </div>
            <div>
              <label className="label">סיבת המסירה</label>
              <textarea
                className="input"
                rows={2}
                value={form.reason}
                onChange={(e) => set("reason", e.target.value)}
              />
            </div>
          </fieldset>
        )}

        {step === 2 && (
          <fieldset className="space-y-4">
            <legend className="font-bold text-brand-dark">בחירת מסלול</legend>
            <div className="grid gap-3">
              <button
                type="button"
                onClick={() => set("surrender_type", "facility")}
                className={`rounded-xl border p-4 text-right transition ${
                  form.surrender_type === "facility"
                    ? "border-brand bg-brand-light ring-2 ring-brand"
                    : "border-gray-300 bg-white"
                }`}
              >
                <span className="block font-bold text-brand-dark">
                  מסירה לפנסיון
                </span>
                <span className="mt-1 block text-sm text-gray-600">
                  הכלב עובר אלינו לפנסיון. אנחנו מטפלים בהעברת הבעלות ומחפשים לו
                  בית חדש ואוהב.
                </span>
              </button>
              <button
                type="button"
                onClick={() => set("surrender_type", "home_subscription")}
                className={`rounded-xl border p-4 text-right transition ${
                  form.surrender_type === "home_subscription"
                    ? "border-brand bg-brand-light ring-2 ring-brand"
                    : "border-gray-300 bg-white"
                }`}
              >
                <span className="block font-bold text-brand-dark">
                  מסירה מהבית
                </span>
                <span className="mt-1 block text-sm text-gray-600">
                  הכלב נשאר אצלכם בבית במהלך החיפוש, במנוי חודשי, בצורה דיסקרטית
                  ורגישה.
                </span>
              </button>
            </div>
          </fieldset>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <ConsentNotice variant="surrender" />

            <div className="space-y-3 text-sm">
              <label className="flex items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1 h-5 w-5"
                  checked={form.privacy_required}
                  onChange={(e) => set("privacy_required", e.target.checked)}
                />
                <span>אבקש טיפול דיסקרטי בפנייה</span>
              </label>
              <label className="flex items-start gap-3">
                <input
                  type="checkbox"
                  className="mt-1 h-5 w-5"
                  checked={form.allow_direct_contact}
                  onChange={(e) =>
                    set("allow_direct_contact", e.target.checked)
                  }
                />
                <span>
                  מאשר/ת שמאמצים פוטנציאליים ייצרו איתי קשר ישיר (רלוונטי למסירה
                  מהבית)
                </span>
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
                label="צילום תעודת זהות"
                documentType="id_card_surrenderer"
                hint="נדרש לצורך העברת בעלות מול הרשות."
              />
              <DocumentUpload
                label="תמונה שלכם עם הכלב"
                documentType="other"
                hint="עוזר לנו להכיר את הכלב ולהתאים לו בית."
              />
            </div>
          </div>
        )}

        {error && <p className="text-sm font-medium text-red-600">{error}</p>}

        <div className="flex gap-3 pt-1">
          {step > 0 && (
            <button
              type="button"
              onClick={back}
              className="btn-outline flex-1 py-3 text-base"
            >
              חזרה
            </button>
          )}
          {step < STEPS.length - 1 ? (
            <button
              type="button"
              onClick={next}
              className="btn-primary flex-1 py-3 text-base"
            >
              המשך
            </button>
          ) : (
            <button
              type="button"
              onClick={onSubmit}
              disabled={submitting}
              className="btn-primary flex-1 py-3 text-base disabled:opacity-60"
            >
              {submitting ? "שולח…" : "שליחת פנייה"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
