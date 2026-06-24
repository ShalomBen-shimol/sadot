import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "פנסיון בשדות — מסירה ואימוץ כלבים",
  description: "מסירה רגישה ואימוץ אחראי של כלבים, בליווי מלא של פנסיון בשדות.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl">
      <body>
        <header className="border-b bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
            <Link href="/" className="text-xl font-bold text-brand">
              🐾 פנסיון בשדות
            </Link>
            <nav className="flex gap-4 text-sm">
              <Link href="/adopt" className="hover:text-brand">אימוץ כלב</Link>
              <Link href="/surrender" className="hover:text-brand">מסירת כלב</Link>
              <Link href="/admin" className="text-gray-500 hover:text-brand">ניהול</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="mt-12 border-t bg-white py-6 text-center text-sm text-gray-500">
          פנסיון בשדות · מערכת CRM ואוטומציה · שלב 1 (MVP)
        </footer>
      </body>
    </html>
  );
}
