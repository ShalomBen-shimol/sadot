"use client";

import { useState } from "react";

// Photo gallery for the dog profile. Shows a large active image with a thumbnail
// strip below. Falls back gracefully to a single placeholder when there are no
// photos. `photos` is the DogPublic.photos[] array.
export default function DogGallery({
  photos,
  alt,
  fallback,
}: {
  photos: string[];
  alt: string;
  fallback: string;
}) {
  const images = photos.length > 0 ? photos : [fallback];
  const [active, setActive] = useState(0);
  const current = images[Math.min(active, images.length - 1)];

  return (
    <div className="space-y-3">
      <div className="aspect-[4/3] w-full overflow-hidden rounded-xl bg-gray-100">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={current} alt={alt} className="h-full w-full object-cover" />
      </div>

      {images.length > 1 && (
        <div className="flex flex-wrap gap-2">
          {images.map((src, i) => (
            <button
              key={`${src}-${i}`}
              type="button"
              onClick={() => setActive(i)}
              aria-label={`תמונה ${i + 1}`}
              aria-current={i === active}
              className={`h-16 w-16 overflow-hidden rounded-lg border-2 transition ${
                i === active
                  ? "border-brand"
                  : "border-transparent opacity-70 hover:opacity-100"
              }`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={src} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
