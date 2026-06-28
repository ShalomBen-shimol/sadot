import type { Metadata } from "next";
import DogCatalog from "@/components/DogCatalog";
import { getPublicDogs } from "@/lib/api";

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

export default async function AdoptPage() {
  let dogs = [] as Awaited<ReturnType<typeof getPublicDogs>>;
  let error: string | null = null;
  try {
    dogs = await getPublicDogs();
  } catch {
    error = "לא ניתן לטעון את רשימת הכלבים כרגע. נסו לרענן בעוד מספר רגעים.";
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-brand-dark sm:text-3xl">כלבים לאימוץ</h1>
        <p className="mt-2 max-w-2xl text-gray-600">
          כל כלב מגיע עם סל אימוץ נדיב וליווי מלא. לחצו על כלב לפרטים ולהשארת פנייה.
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
    </div>
  );
}
