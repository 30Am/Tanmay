"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const ROUTES = [
  { href: "/app", tile: "bg-gradient-sunrise", label: "Home" },
  { href: "/app/content", tile: "bg-butter", label: "Content" },
  { href: "/app/ads", tile: "bg-coral/70", label: "Ads" },
  { href: "/app/qa", tile: "bg-periwinkle", label: "Q&A" },
  { href: "#", tile: "bg-mint", label: "History" },
  { href: "#", tile: "bg-lilac", label: "Templates" },
];

/** 80px icon-only sidebar used on tool screens (matches Figma 05/06/07). */
export default function IconSidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-20 shrink-0 bg-bg border-r border-border/60 h-screen sticky top-0 flex flex-col items-center py-6">
      <Link href="/" className="h-10 w-10 rounded-[10px] bg-gradient-sunrise shadow-card" aria-label="Home" />
      <div className="h-px w-8 bg-border mt-5" />
      <nav className="mt-5 flex flex-col gap-2">
        {ROUTES.map((r) => {
          const active = pathname === r.href;
          return (
            <Link
              key={r.label}
              href={r.href}
              title={r.label}
              className={cn(
                "h-12 w-12 rounded-[12px] grid place-items-center transition",
                active ? "ring-2 ring-ink/70 ring-offset-2 ring-offset-bg" : "hover:ring-2 hover:ring-border hover:ring-offset-2 hover:ring-offset-bg",
              )}
            >
              <span className={cn("h-7 w-7 rounded-[8px]", r.tile)} aria-hidden />
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
