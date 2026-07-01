import type { Metadata } from "next";
import DogCatalog from "@/components/DogCatalog";
import { getPublicDogs } from "@/lib/api";
import { BRAND } from "@/lib/brand";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "כלבים לאימוץ — פנסיון בשדות",
  description:
    "כלבים מקסימים מחפשים בית אוהב. כל כלב מגיע עם סל אימוץ נדיב וליווי מלא. סננו לפי גודל, אזור והתאמה לילדים ולכלבים אחרים.",
  openGraph: {
    title: "כלבים לאימוץ — פנסיון בשדות",
    description:
      "כלבים מקסימים מחפשים בית אוהב. כל כלב מגיע עם סל אימוץ נדיב וליווי מלא.",
    type: "website",
  },
};

// Adoption FAQ — mirrors the copy from the original basadot site.
const FAQ: { q: string; a: string }[] = [
  {
    q: "כמה עולה אימוץ?",
    a: "דמי האימוץ הם 700 ₪ ומעלה, בהתאם לכלב. הסכום מכסה עיקור/סירוס, חיסונים, שבב וסל אימוץ מלא לתחילת הדרך.",
  },
  {
    q: "מה כולל סל האימוץ?",
    a: "כל כלב יוצא לדרך עם סל נדיב: מזון להתחלה, קערות, רצועה ורתמה, מיטה או שמיכה, וליווי צמוד שלנו גם אחרי האימוץ.",
  },
  {
    q: "איך מתנהל יום האימוץ?",
    a: "לאחר שאתם משאירים פנייה על כלב, ניצור קשר לתיאום היכרות. יום האימוץ מתקיים בתיאום מראש, ואנחנו כאן לכל שאלה בהמשך הדרך.",
  },
  {
    q: "האם אפשר לאמץ אם יש לי ילדים או כלב נוסף?",
    a: "בהחלט. לכל כלב מצוין אם הוא מתאים לילדים ומסתדר עם כלבים אחרים — השתמשו בסינון כדי למצוא את ההתאמה הנכונה עבורכם.",
  },
];

// Three-step "how it works", matching the original site's flow.
const STEPS: { icon: string; title: string; text: string }[] = [
  { icon: "🐕", title: "בוחרים כלב", text: "מעיינים בכלבים הזמינים ומוצאים את זה שמדבר אליכם." },
  { icon: "📝", title: "משאירים פנייה", text: "ממלאים פרטים קצרים ואנחנו חוזרים אליכם לתיאום היכרות." },
  { icon: "🏡", title: "מביאים הביתה", text: "אחרי היכרות מוצלחת — הכלב יוצא אליכם עם סל אימוץ מלא." },
];

export default async function AdoptPage() {
  let dogs = [] as Awaited<ReturnType<typeof getPublicDogs>>;
  let error: string | null = null;
  try {
    dogs = await getPublicDogs();
  } catch {
    error = "לא ניתן לטעון את רשימת הכלבים כרגע. נסו לרענן בעוד מספר רגעים.";
  }

  return (
    <div className="space-y-12">
      {/* Hero — reuses the original site's banner image + logo */}
      <section className="relative overflow-hidden rounded-3xl bg-brand-dark text-white shadow-md">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={BRAND.heroAdopt}
          alt=""
          className="absolute inset-0 h-full w-full object-cover opacity-40"
        />
        <div className="relative flex flex-col items-center gap-4 px-6 py-14 text-center sm:py-20">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={BRAND.logo}
            alt={BRAND.name}
            className="h-20 w-20 rounded-full bg-white/90 p-1 shadow-lg sm:h-24 sm:w-24"
          />
          <h1 className="text-3xl font-bold drop-shadow sm:text-5xl">אמצו כלב</h1>
          <p className="max-w-2xl text-base text-white/90 sm:text-lg">
            כלבים מקסימים מחפשים בית אוהב. כל כלב מגיע עם סל אימוץ נדיב וליווי מלא של פנסיון בשדות.
          </p>
          <a
            href="#catalog"
            className="mt-2 rounded-full bg-white px-8 py-3 font-semibold text-brand-dark shadow transition hover:bg-brand-light"
          >
            לכלבים שלנו ←
          </a>
        </div>
      </section>

      {/* How it works */}
      <section className="grid gap-4 sm:grid-cols-3">
        {STEPS.map((s, i) => (
          <div key={i} className="card text-center">
            <div className="text-3xl">{s.icon}</div>
            <h3 className="mt-2 font-bold text-brand-dark">{s.title}</h3>
            <p className="mt-1 text-sm text-gray-600">{s.text}</p>
          </div>
        ))}
      </section>

      {/* Catalog */}
      <section id="catalog" className="scroll-mt-6 space-y-6">
        <header>
          <h2 className="text-2xl font-bold text-brand-dark sm:text-3xl">הכלבים שלנו</h2>
          <p className="mt-2 max-w-2xl text-gray-600">
            לחצו על כלב לפרטים ולהשארת פנייה. אפשר לסנן לפי גודל, אזור והתאמה לילדים ולכלבים אחרים.
          </p>
        </header>

        {error ? (
          <div className="card text-red-600">{error}</div>
        ) : dogs.length === 0 ? (
          <div className="card text-center text-gray-500">
            אין כרגע כלבים זמינים לאימוץ. בקרוב יתווספו עוד 🐾
          </div>
        ) : (
          <DogCatalog dogs={dogs} />
        )}
      </section>

      {/* FAQ */}
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-brand-dark sm:text-3xl">שאלות נפוצות</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {FAQ.map((item, i) => (
            <div key={i} className="card">
              <h3 className="font-bold text-brand-dark">{item.q}</h3>
              <p className="mt-2 text-sm leading-relaxed text-gray-600">{item.a}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
