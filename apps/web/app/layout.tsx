import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Create with Tanmay",
  description: "Three creator tools, one persona core.",
};

const tabs = [
  { href: "/content", label: "Content" },
  { href: "/ad", label: "Ad" },
  { href: "/qa", label: "Q&A" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <header className="flex items-center justify-between border-b border-border pb-6">
            <Link href="/" className="flex items-center gap-3">
              <span className="font-mono text-xs uppercase tracking-[0.3em] text-accent">Create with</span>
              <span className="text-2xl font-bold tracking-tight">Tanmay</span>
            </Link>
            <nav className="flex gap-1 rounded-full border border-border bg-panel p-1">
              {tabs.map((t) => (
                <Link
                  key={t.href}
                  href={t.href}
                  className="rounded-full px-4 py-1.5 text-sm text-muted transition hover:text-white"
                >
                  {t.label}
                </Link>
              ))}
            </nav>
          </header>
          <main className="py-10">{children}</main>
        </div>
      </body>
    </html>
  );
}
