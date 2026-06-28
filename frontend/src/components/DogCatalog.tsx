"use client";

import { useMemo, useState } from "react";
import DogCard from "@/components/DogCard";
import type { DogPublic, DogSize } from "@/lib/api";
import { SIZE_LABELS } from "@/lib/dogLabels";

type Filters = {
  size: DogSize | "all";
  area: string;
  goodWithChildren: boolean;
  goodWithDogs: boolean;
};

const INITIAL: Filters = {
  size: "all",
  area: "all",
  goodWithChildren: false,
  goodWithDogs: false,
};

export default function DogCatalog({ dogs }: { dogs: DogPublic[] }) {
  const [filters, setFilters] = useState<Filters>(INITIAL);

  // Distinct, sorted areas present in the current dog list.
  const areas = useMemo(() => {
    const set = new Set<string>();
    for (const dog of dogs) {
      if (dog.public_area) set.add(dog.public_area);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, "he"));
  }, [dogs]);

  const filtered = useMemo(() => {
    return dogs.filter((dog) => {
      if (filters.size !== "all" && dog.size !== filters.size) return false;
      if (filters.area !== "all" && dog.public_area !== filters.area) return false;
      if (filters.goodWithChildren && dog.good_with_children !== true) return false;
      if (filters.goodWithDogs && dog.good_with_dogs !== true) return false;
      return true;
    });
  }, [dogs, filters]);

  function set<K extends keyof Filters>(key: K, value: Filters[K]) {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  const hasActiveFilters =
    filters.size !== "all" ||
    filters.area !== "all" ||
    filters.goodWithChildren ||
    filters.goodWithDogs;

  return (
    <div className="space-y-6">
      <div className="card flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end">
        <div className="sm:w-40">
          <label className="label" htmlFor="filter-size">
            גודל
          </label>
          <select
            id="filter-size"
            className="input"
            value={filters.size}
            onChange={(e) => set("size", e.target.value as Filters["size"])}
          >
            <option value="all">הכול</option>
            {(Object.keys(SIZE_LABELS) as DogSize[]).map((size) => (
              <option key={size} value={size}>
                {SIZE_LABELS[size]}
              </option>
            ))}
          </select>
        </div>

        {areas.length > 0 && (
          <div className="sm:w-48">
            <label className="label" htmlFor="filter-area">
              אזור
            </label>
            <select
              id="filter-area"
              className="input"
              value={filters.area}
              onChange={(e) => set("area", e.target.value)}
            >
              <option value="all">כל האזורים</option>
              {areas.map((area) => (
                <option key={area} value={area}>
                  {area}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex flex-wrap gap-4 text-sm sm:pb-2.5">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              className="h-5 w-5 accent-brand"
              checked={filters.goodWithChildren}
              onChange={(e) => set("goodWithChildren", e.target.checked)}
            />
            מתאים לילדים
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              className="h-5 w-5 accent-brand"
              checked={filters.goodWithDogs}
              onChange={(e) => set("goodWithDogs", e.target.checked)}
            />
            מסתדר עם כלבים
          </label>
        </div>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={() => setFilters(INITIAL)}
            className="text-sm font-medium text-brand hover:underline sm:mr-auto sm:pb-2.5"
          >
            ניקוי סינון
          </button>
        )}
      </div>

      <p className="text-sm text-gray-500">
        {filtered.length === dogs.length
          ? `${dogs.length} כלבים זמינים`
          : `נמצאו ${filtered.length} מתוך ${dogs.length} כלבים`}
      </p>

      {filtered.length === 0 ? (
        <div className="card text-center text-gray-500">
          לא נמצאו כלבים שמתאימים לסינון. נסו להרחיב את החיפוש 🐾
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((dog) => (
            <DogCard key={dog.id} dog={dog} />
          ))}
        </div>
      )}
    </div>
  );
}
