import Link from "next/link";
import { notFound } from "next/navigation";
import AdoptionForm from "@/components/AdoptionForm";
import { getPublicDog } from "@/lib/api";

export const dynamic = "force-dynamic";

function yn(v: boolean | null): string {
  if (v === null) return "לא ידוע";
  return v ? "כן" : "לא";
}

export default async function DogDetail({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  let dog;
  try {
    dog = await getPublicDog(id);
  } catch {
    notFound();
  }

  const photo = dog.photos[0] || "https://placedog.net/800/500";

  return (
    <div className="space-y-6">
      <Link href="/adopt" className="text-sm text-brand hover:underline">→ חזרה לכל הכלבים</Link>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={photo} alt={dog.name || "כלב"} className="w-full rounded-xl object-cover" />
        </div>
        <div className="space-y-3">
          <h1 className="text-2xl font-bold text-brand-dark">{dog.name || "כלב ללא שם"}</h1>
          {dog.current_location_type === "home" && <span className="badge">נמצא בבית המוסר</span>}
          <p className="text-gray-700">{dog.public_description || "כלב מקסים שמחפש בית אוהב."}</p>
          <ul className="space-y-1 text-sm text-gray-600">
            <li>גזע: {dog.breed || "מעורב"}</li>
            <li>גיל: {dog.age != null ? `${dog.age} שנים` : "לא ידוע"}</li>
            <li>אזור: {dog.public_area || "לא צוין"}</li>
            <li>מתאים לילדים: {yn(dog.good_with_children)}</li>
            <li>מסתדר עם כלבים: {yn(dog.good_with_dogs)}</li>
            <li>מתאים לדירה: {yn(dog.suitable_for_apartment)}</li>
          </ul>
          <div className="rounded-lg bg-brand-light p-3 text-sm text-brand-dark">
            🎁 סל אימוץ נדיב: חיסונים, אוכל לחודש, ליווי והטבות חנות.
          </div>
        </div>
      </div>

      <AdoptionForm dogId={dog.id} />
    </div>
  );
}
