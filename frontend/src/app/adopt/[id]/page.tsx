import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import AdoptionForm from "@/components/AdoptionForm";
import DogGallery from "@/components/DogGallery";
import { getPublicDog, type DogPublic } from "@/lib/api";
import {
  ageLabel,
  dogPhoto,
  genderLabel,
  positiveTraits,
  sizeLabel,
  yesNo,
} from "@/lib/dogLabels";

export const dynamic = "force-dynamic";

const BASKET_ITEMS = [
  "חיסונים וטיפול וטרינרי ראשוני",
  "שק אוכל איכותי לחודש הראשון",
  "ליווי מקצועי לאורך הקליטה",
  "הטבות בחנות לחיות מחמד",
];

async function loadDog(id: number): Promise<DogPublic | null> {
  if (!Number.isFinite(id)) return null;
  try {
    return await getPublicDog(id);
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: { id: string };
}): Promise<Metadata> {
  const dog = await loadDog(Number(params.id));
  if (!dog) {
    return { title: "כלב לא נמצא — פנסיון בשדות" };
  }
  const name = dog.name || "כלב לאימוץ";
  const description =
    dog.public_description ||
    `${name} מחפש בית אוהב. ${dog.breed || "מעורב"}, ${ageLabel(dog.age)}. מגיע עם סל אימוץ נדיב וליווי מלא.`;
  const image = dogPhoto(dog, "800/600");
  return {
    title: `${name} — אימוץ כלב | פנסיון בשדות`,
    description,
    openGraph: {
      title: `${name} מחפש בית — פנסיון בשדות`,
      description,
      type: "article",
      images: [{ url: image }],
    },
  };
}

function Trait({ label, value }: { label: string; value: boolean | null }) {
  return (
    <li className="flex items-center justify-between border-b border-gray-100 py-1.5 last:border-0">
      <span className="text-gray-600">{label}</span>
      <span className="font-medium text-gray-800">{yesNo(value)}</span>
    </li>
  );
}

export default async function DogDetail({ params }: { params: { id: string } }) {
  const dog = await loadDog(Number(params.id));
  if (!dog) notFound();

  const name = dog.name || "כלב ללא שם";
  const traits = positiveTraits(dog);
  const fallback = dogPhoto(dog, "800/600");

  return (
    <div className="space-y-8">
      <Link href="/adopt" className="inline-block text-sm text-brand hover:underline">
        חזרה לכל הכלבים →
      </Link>

      <div className="grid gap-8 md:grid-cols-2">
        <DogGallery photos={dog.photos} alt={name} fallback={fallback} />

        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-bold text-brand-dark sm:text-3xl">{name}</h1>
            {dog.current_location_type === "home" && (
              <span className="badge">נמצא בבית המוסר</span>
            )}
          </div>

          <p className="leading-relaxed text-gray-700">
            {dog.public_description || "כלב מקסים שמחפש בית חם ואוהב. צרו קשר כדי להכיר אותו."}
          </p>

          {traits.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {traits.map((t) => (
                <span key={t.key} className="badge">
                  {t.label}
                </span>
              ))}
            </div>
          )}

          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <div>
              <dt className="text-gray-500">גזע</dt>
              <dd className="font-medium text-gray-800">{dog.breed || "מעורב"}</dd>
            </div>
            <div>
              <dt className="text-gray-500">גיל</dt>
              <dd className="font-medium text-gray-800">{ageLabel(dog.age)}</dd>
            </div>
            <div>
              <dt className="text-gray-500">מין</dt>
              <dd className="font-medium text-gray-800">{genderLabel(dog.gender)}</dd>
            </div>
            <div>
              <dt className="text-gray-500">גודל</dt>
              <dd className="font-medium text-gray-800">{sizeLabel(dog.size)}</dd>
            </div>
            {dog.color && (
              <div>
                <dt className="text-gray-500">צבע</dt>
                <dd className="font-medium text-gray-800">{dog.color}</dd>
              </div>
            )}
            {dog.public_area && (
              <div>
                <dt className="text-gray-500">אזור</dt>
                <dd className="font-medium text-gray-800">{dog.public_area}</dd>
              </div>
            )}
          </dl>

          <div className="rounded-xl bg-brand-light p-4">
            <p className="font-semibold text-brand-dark">🎁 סל אימוץ נדיב</p>
            <ul className="mt-2 space-y-1 text-sm text-brand-dark">
              {BASKET_ITEMS.map((item) => (
                <li key={item} className="flex gap-2">
                  <span aria-hidden>✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <a href="#adoption-form" className="btn-primary w-full sm:w-auto">
            אני רוצה לאמץ את {name}
          </a>
        </div>
      </div>

      <section className="card">
        <h2 className="mb-3 text-lg font-bold text-brand-dark">התאמה למשפחה</h2>
        <ul className="text-sm">
          <Trait label="מתאים לילדים" value={dog.good_with_children} />
          <Trait label="מסתדר עם כלבים אחרים" value={dog.good_with_dogs} />
          <Trait label="מסתדר עם חתולים" value={dog.good_with_cats} />
          <Trait label="מתאים לדירה" value={dog.suitable_for_apartment} />
          <Trait label="מתאים למאמצים מתחילים" value={dog.suitable_for_first_time_owner} />
        </ul>
      </section>

      <section id="adoption-form" className="scroll-mt-6">
        <AdoptionForm dogId={dog.id} />
      </section>
    </div>
  );
}
