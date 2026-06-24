import DogCard from "@/components/DogCard";
import { getPublicDogs } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AdoptPage() {
  let dogs = [] as Awaited<ReturnType<typeof getPublicDogs>>;
  let error: string | null = null;
  try {
    dogs = await getPublicDogs();
  } catch (e) {
    error = "לא ניתן לטעון את רשימת הכלבים כרגע.";
  }

  return (
    <div>
      <h1 className="mb-2 text-2xl font-bold text-brand-dark">כלבים לאימוץ</h1>
      <p className="mb-6 text-gray-600">
        כל כלב מגיע עם סל אימוץ נדיב וליווי מלא. לחצו על כלב לפרטים והשארת פנייה.
      </p>

      {error && <div className="card text-red-600">{error}</div>}
      {!error && dogs.length === 0 && (
        <div className="card text-gray-500">אין כרגע כלבים זמינים לאימוץ. בקרוב יתווספו עוד 🐾</div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {dogs.map((dog) => (
          <DogCard key={dog.id} dog={dog} />
        ))}
      </div>
    </div>
  );
}
