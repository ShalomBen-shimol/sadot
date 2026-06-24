import Link from "next/link";
import type { DogPublic } from "@/lib/api";

const SIZE_LABELS: Record<string, string> = {
  small: "קטן",
  medium: "בינוני",
  large: "גדול",
  xlarge: "גדול מאוד",
};

export default function DogCard({ dog }: { dog: DogPublic }) {
  const photo = dog.photos[0] || "https://placedog.net/600/400";
  return (
    <Link href={`/adopt/${dog.id}`} className="card block transition hover:shadow-md">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={photo} alt={dog.name || "כלב"} className="mb-3 h-44 w-full rounded-lg object-cover" />
      <div className="flex items-center justify-between">
        <h3 className="font-bold">{dog.name || "כלב ללא שם"}</h3>
        {dog.current_location_type === "home" && (
          <span className="badge">נמצא בבית המוסר</span>
        )}
      </div>
      <p className="mt-1 text-sm text-gray-600">
        {dog.breed || "מעורב"}
        {dog.age != null ? ` · ${dog.age} שנים` : ""}
        {dog.size ? ` · ${SIZE_LABELS[dog.size] ?? dog.size}` : ""}
      </p>
      {dog.public_area && <p className="mt-1 text-xs text-gray-500">אזור: {dog.public_area}</p>}
    </Link>
  );
}
