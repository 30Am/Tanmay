"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Logo from "@/components/ui/Logo";
import UserMenu from "@/components/workspace/UserMenu";
import { cn } from "@/lib/utils";

const CREATE = [
  { href: "/app", label: "Dashboard", dot: "bg-gradient-sunrise" },
  { href: "/app/content", label: "Content", dot: "bg-coral/80" },
  { href: "/app/ads", label: "Ads", dot: "bg-lavender" },
  { href: "/app/qa", label: "Q&A", dot: "bg-mint" },
];

const WORKSPACE = [
  { href: "/app/history", label: "History", dot: "bg-periwinkle" },
  { href: "#", label: "Templates", dot: "bg-lilac" },
  { href: "#", label: "Tone dial", dot: "bg-aqua" },
  { href: "#", label: "Extension", dot: "bg-peach", tag: "NEW" },
];

const ACCOUNT = [
  { href: "#", label: "Billing", dot: "bg-butter" },
  { href: "#", label: "Settings", dot: "bg-blush" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-[260px] shrink-0 bg-bg border-r border-border/60 h-screen sticky top-0 overflow-y-auto">
      <div className="p-5">
        <Logo size="md" />
      </div>

      <div className="px-5">
        <Link
          href="/app/content"
          className="w-full flex items-center justify-center gap-2 bg-ink text-surface rounded-pill py-3 text-[14px] font-medium hover:translate-y-[-1px] hover:shadow-soft transition"
        >
          <span className="text-[18px] leading-none">+</span>
          New generation
        </Link>
      </div>

      <nav className="px-5 py-8 space-y-8">
        <Section title="CREATE" items={CREATE} pathname={pathname} />
        <Section title="WORKSPACE" items={WORKSPACE} pathname={pathname} />
        <Section title="ACCOUNT" items={ACCOUNT} pathname={pathname} />
      </nav>

      <div className="mt-auto p-5">
        <UserMenu />
      </div>
    </aside>
  );
}

function Section({
  title,
  items,
  pathname,
}: {
  title: string;
  items: { href: string; label: string; dot: string; tag?: string }[];
  pathname: string | null;
}) {
  return (
    <div>
      <div className="text-[11px] font-semibold tracking-[0.16em] text-ink-3 px-3 mb-2">{title}</div>
      <ul className="space-y-0.5">
        {items.map((it) => {
          const active = pathname === it.href;
          return (
            <li key={it.label}>
              <Link
                href={it.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-[14px] transition",
                  active ? "bg-surface border border-border text-ink shadow-card" : "text-ink-2 hover:bg-surface/60",
                )}
              >
                <span className={cn("h-[22px] w-[22px] rounded-[7px] shrink-0", it.dot)} />
                <span className="flex-1">{it.label}</span>
                {it.tag && (
                  <span className="text-[10px] font-semibold tracking-wide bg-coral/25 text-coral-deep px-2 py-0.5 rounded-pill">
                    {it.tag}
                  </span>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
