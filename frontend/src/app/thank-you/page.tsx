import Link from "next/link";

export default function ThankYou({ searchParams }: { searchParams: { type?: string } }) {
  const isSurrender = searchParams.type === "surrender";
  return (
    <div className="card mx-auto max-w-lg text-center">
      <div className="text-4xl">🐾</div>
      <h1 className="mt-3 text-2xl font-bold text-brand-dark">פנייתכם התקבלה!</h1>
      <p className="mt-3 text-gray-600">
        {isSurrender
          ? "נציג מטעמנו ייצור איתכם קשר בקרוב כדי ללוות אתכם בתהליך ברגישות מלאה."
          : "תודה על העניין באימוץ! נחזור אליכם עם פרטים על הכלב ועל סל האימוץ."}
      </p>
      <Link href="/" className="btn-primary mt-6">חזרה לדף הבית</Link>
    </div>
  );
}
