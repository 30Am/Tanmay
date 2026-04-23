"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/app/content", label: "Content", dot: "bg-coral-deep", activeBg: "bg-coral/25" },
  { href: "/app/ads", label: "Ads", dot: "bg-[#7d6ec6]", activeBg: "bg-lavender/70" },
  { href: "/app/qa", label: "Q&A", dot: "bg-[#2e9a7a]", activeBg: "bg-mint/70" },
];

/** Tab pill row that sits in the top-bar of each tool screen. */
export default function TabSwitcher() {
  const pathname = usePathname();
  return (
    <div className="inline-flex items-center gap-1 rounded-pill border border-border bg-surface p-1.5">
      {TABS.map((t) => {
        const active = pathname?.startsWith(t.href);
        return (
          <Link
            key={t.href}
            href={t.href}
            className={cn(
              "flex items-center gap-2 rounded-pill px-4 py-1.5 text-[14px] font-medium transition",
              active ? `${t.activeBg} text-ink` : "text-ink-2 hover:text-ink",
            )}
          >
            <span className={cn("h-1.5 w-1.5 rounded-full", t.dot)} />
            {t.label}
          </Link>
        );
      })}
    </div>
  );
}
