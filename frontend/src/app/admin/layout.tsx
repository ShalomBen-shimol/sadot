"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "./_components/ui";

const NAV: { href: string; label: string }[] = [
  { href: "/admin", label: "לוח בקרה" },
  { href: "/admin/surrender-cases", label: "תיקי מסירה" },
  { href: "/admin/adoption-cases", label: "תיקי אימוץ" },
  { href: "/admin/dogs", label: "כלבים" },
  { href: "/admin/ownership-transfers", label: "העברות בעלות" },
  { href: "/admin/authorities", label: "רשויות וטרינריות" },
  { href: "/admin/settings", label: "הגדרות" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  // The login screen is rendered without the back-office chrome.
  if (pathname === "/admin/login") {
    return <>{children}</>;
  }

  function isActive(href: string): boolean {
    if (href === "/admin") return pathname === "/admin";
    return pathname.startsWith(href);
  }

  function logout() {
    clearToken();
    router.replace("/admin/login");
  }

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      <aside className="lg:w-56 lg:shrink-0">
        <nav className="card flex flex-row flex-wrap gap-2 lg:flex-col lg:gap-1">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                isActive(item.href)
                  ? "bg-brand text-white"
                  : "text-gray-700 hover:bg-brand-light hover:text-brand-dark"
              }`}
            >
              {item.label}
            </Link>
          ))}
          <button
            onClick={logout}
            className="mt-2 rounded-lg px-3 py-2 text-right text-sm font-medium text-gray-500 hover:bg-gray-100 hover:text-red-600"
          >
            התנתקות
          </button>
        </nav>
      </aside>
      <div className="min-w-0 flex-1 space-y-6">{children}</div>
    </div>
  );
}
