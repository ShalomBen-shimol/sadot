// Shared display helpers for the public adoption catalog and dog profile.
// Keeps Hebrew labels and trait derivation in one place so the catalog grid,
// DogCard and the /adopt/[id] profile stay consistent.

import type { DogPublic, DogSize, DogGender } from "@/lib/api";

export const SIZE_LABELS: Record<DogSize, string> = {
  small: "קטן",
  medium: "בינוני",
  large: "גדול",
  xlarge: "גדול מאוד",
};

export const GENDER_LABELS: Record<DogGender, string> = {
  male: "זכר",
  female: "נקבה",
  unknown: "לא ידוע",
};

export function sizeLabel(size: DogSize | null): string {
  return size ? SIZE_LABELS[size] ?? size : "לא צוין";
}

export function genderLabel(gender: DogGender): string {
  return GENDER_LABELS[gender] ?? "לא ידוע";
}

export function ageLabel(age: number | null): string {
  if (age == null) return "גיל לא ידוע";
  if (age < 1) return "גור";
  return age === 1 ? "שנה" : `${age} שנים`;
}

// Yes/No/Unknown for the detailed traits table.
export function yesNo(value: boolean | null): string {
  if (value === null) return "לא ידוע";
  return value ? "כן" : "לא";
}

// Deterministic placeholder so cards/gallery don't show a broken image when a
// dog has no photos yet. Sized per usage to keep aspect ratios sharp.
export function dogPhoto(dog: Pick<DogPublic, "id" | "photos">, size = "600/400"): string {
  return dog.photos[0] || `https://placedog.net/${size}?id=${dog.id}`;
}

export type DogTrait = { key: string; label: string };

// Positive selling-point badges — only the traits explicitly marked true.
export function positiveTraits(dog: DogPublic): DogTrait[] {
  const traits: DogTrait[] = [];
  if (dog.good_with_children) traits.push({ key: "children", label: "מתאים לילדים" });
  if (dog.good_with_dogs) traits.push({ key: "dogs", label: "מסתדר עם כלבים" });
  if (dog.good_with_cats) traits.push({ key: "cats", label: "מסתדר עם חתולים" });
  if (dog.suitable_for_apartment) traits.push({ key: "apartment", label: "מתאים לדירה" });
  if (dog.suitable_for_first_time_owner)
    traits.push({ key: "first_time", label: "מתאים למאמצים מתחילים" });
  return traits;
}
