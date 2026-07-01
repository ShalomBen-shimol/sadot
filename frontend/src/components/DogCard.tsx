import Link from "next/link";
import type { DogPublic } from "@/lib/api";
import { ageLabel, dogPhoto, positiveTraits, sizeLabel } from "@/lib/dogLabels";

export default function DogCard({ dog }: { dog: DogPublic }) {
  const photo = dogPhoto(dog);
  const traits = positiveTraits(dog).slice(0, 3);
  const meta = [dog.breed || "מעורב", ageLabel(dog.age), sizeLabel(dog.size)]
    .filter(Boolean)
    .join(" · ");

  return (
    <Link
      href={`/adopt/${dog.id}`}
      className="card group flex flex-col overflow-hidden p-0 transition hover:-translate-y-0.5 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-brand"
    >
      <div className="relative h-48 w-full overflow-hidden bg-gray-100">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={photo}
          alt={dog.name || "כלב לאימוץ"}
          loading="lazy"
          className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
        />
        {dog.current_location_type === "home" && (
          <span className="badge absolute right-2 top-2 bg-white/90 shadow-sm">
            נמצא בבית המוסר
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col p-4">
        <h3 className="text-lg font-bold text-brand-dark">{dog.name || "כלב ללא שם"}</h3>
        <p className="mt-1 text-sm text-gray-600">{meta}</p>
        {dog.public_area && (
          <p className="mt-1 text-xs text-gray-500">אזור: {dog.public_area}</p>
        )}

        {traits.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {traits.map((t) => (
              <span
                key={t.key}
                className="rounded-full bg-brand-light px-2.5 py-0.5 text-xs font-medium text-brand-dark"
              >
                {t.label}
              </span>
            ))}
          </div>
        )}

        <span className="btn-primary mt-4 w-full justify-center text-sm group-hover:bg-brand-dark">
          קחו אותי הביתה 🏡
        </span>
      </div>
    </Link>
  );
}
