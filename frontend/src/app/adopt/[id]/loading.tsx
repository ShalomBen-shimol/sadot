export default function DogDetailLoading() {
  return (
    <div className="space-y-8">
      <div className="h-4 w-32 animate-pulse rounded bg-gray-200" />
      <div className="grid gap-8 md:grid-cols-2">
        <div className="aspect-[4/3] w-full animate-pulse rounded-xl bg-gray-200" />
        <div className="space-y-4">
          <div className="h-8 w-1/2 animate-pulse rounded bg-gray-200" />
          <div className="h-4 w-full animate-pulse rounded bg-gray-200" />
          <div className="h-4 w-5/6 animate-pulse rounded bg-gray-200" />
          <div className="h-24 w-full animate-pulse rounded-xl bg-gray-200" />
          <div className="h-10 w-48 animate-pulse rounded-lg bg-gray-200" />
        </div>
      </div>
    </div>
  );
}
