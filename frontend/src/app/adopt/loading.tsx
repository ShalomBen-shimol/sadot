export default function AdoptLoading() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
        <div className="h-4 w-80 max-w-full animate-pulse rounded bg-gray-200" />
      </div>
      <div className="card h-20 animate-pulse" />
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="card overflow-hidden p-0">
            <div className="h-48 w-full animate-pulse bg-gray-200" />
            <div className="space-y-2 p-4">
              <div className="h-5 w-2/3 animate-pulse rounded bg-gray-200" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-gray-200" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
