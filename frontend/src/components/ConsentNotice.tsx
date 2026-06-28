"use client";

// Reusable privacy/consent notice for the public QR intake forms.
//
// Explains, per the Israeli Privacy Protection Law (incl. תיקון 13):
//   - purpose of collection
//   - who the data may be shared with (authorities / adopter)
//   - the data subject's rights
//
// `variant` tailors the "who receives the data" wording to the flow.

type ConsentVariant = "surrender" | "adoption";

const RECIPIENTS: Record<ConsentVariant, string[]> = {
  surrender: [
    "צוות פנסיון בשדות, לצורך טיפול בפנייה וליווי התהליך.",
    "הרשות המקומית והווטרינר הרשותי, לצורך רישום והעברת בעלות על הכלב.",
    "מאמצים פוטנציאליים — רק אם אישרתם יצירת קשר ישיר (במסלול מסירה מהבית), ורק פרטים הנדרשים להתאמה.",
  ],
  adoption: [
    "צוות פנסיון בשדות, לצורך בדיקת התאמה וליווי תהליך האימוץ.",
    "הרשות המקומית והווטרינר הרשותי, לצורך רישום והעברת הבעלות על הכלב.",
    "בעל הכלב הנוכחי (במסלול מסירה מהבית), לצורך תיאום מפגש והיכרות.",
  ],
};

export default function ConsentNotice({ variant }: { variant: ConsentVariant }) {
  return (
    <div className="rounded-xl border border-brand-light bg-brand-light/40 p-4 text-sm leading-6 text-gray-700">
      <h3 className="mb-2 text-base font-bold text-brand-dark">
        שקיפות ופרטיות (תיקון 13 לחוק הגנת הפרטיות)
      </h3>

      <p className="mb-3">
        אנו אוספים את המידע שתמסרו בטופס זה אך ורק לצורך הטיפול בפנייתכם. המידע
        נשמר באופן מאובטח ולא יימסר לגורמים שאינם נדרשים לתהליך.
      </p>

      <p className="mb-1 font-semibold text-brand-dark">מטרת איסוף המידע</p>
      <p className="mb-3">
        {variant === "surrender"
          ? "טיפול בבקשת המסירה, איתור בית מאמץ מתאים, וביצוע העברת בעלות מול הרשויות."
          : "בדיקת התאמה לאימוץ, תיאום מפגש עם הכלב, וביצוע העברת בעלות מול הרשויות."}
      </p>

      <p className="mb-1 font-semibold text-brand-dark">מי עשוי לקבל את המידע</p>
      <ul className="mb-3 list-disc space-y-1 pr-5">
        {RECIPIENTS[variant].map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>

      <p className="mb-1 font-semibold text-brand-dark">הזכויות שלכם</p>
      <p>
        בכל עת תוכלו לפנות אלינו כדי לעיין במידע שנשמר אודותיכם, לתקן אותו או
        לבקש את מחיקתו, בהתאם לחוק הגנת הפרטיות.
      </p>
    </div>
  );
}
