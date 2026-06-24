import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="rounded-2xl bg-brand-light p-8 text-center">
        <h1 className="text-3xl font-bold text-brand-dark">פנסיון בשדות</h1>
        <p className="mx-auto mt-3 max-w-2xl text-gray-700">
          מסירה רגישה ואימוץ אחראי של כלבים, בליווי מלא ודיסקרטי. אנחנו כאן כדי
          למצוא לכל כלב בית חדש ואוהב.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Link href="/adopt" className="btn-primary">לאימוץ כלב</Link>
          <Link href="/surrender" className="btn-outline">למסירת כלב</Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="card">
          <h3 className="font-bold text-brand-dark">מסירה לפנסיון</h3>
          <p className="mt-2 text-sm text-gray-600">
            הכלב עובר לפנסיון, אנחנו מטפלים בהעברת הבעלות ומחפשים לו בית חדש.
          </p>
        </div>
        <div className="card">
          <h3 className="font-bold text-brand-dark">מסירה מהבית</h3>
          <p className="mt-2 text-sm text-gray-600">
            הכלב נשאר אצלכם בבית במהלך החיפוש, במנוי חודשי, בצורה דיסקרטית ורגישה.
          </p>
        </div>
        <div className="card">
          <h3 className="font-bold text-brand-dark">אימוץ עם סל הטבות</h3>
          <p className="mt-2 text-sm text-gray-600">
            מאמצים מקבלים סל אימוץ נדיב: חיסונים, אוכל לחודש, ליווי והטבות חנות.
          </p>
        </div>
      </section>
    </div>
  );
}
