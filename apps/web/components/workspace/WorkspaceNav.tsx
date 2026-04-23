"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AlignLeft, Box, MessageSquare } from "lucide-react";

const tools = [
  {
    href: "/app/content",
    name: "Content Generation",
    hint: "Reels, threads, cold opens",
    icon: AlignLeft,
    dot: "bg-salmon",
    tint: "bg-salmon/10 text-salmon",
  },
  {
    href: "/app/ad",
    name: "Ad Generation",
    hint: "Sponsor reads with guardrails",
    icon: Box,
    dot: "bg-[#60a5fa]",
    tint: "bg-sky text-[#3a7ab0]",
  },
  {
    href: "/app/qa",
    name: "How Would Tanmay Answer",
    hint: "Grounded, cited answers",
    icon: MessageSquare,
    dot: "bg-lavenderDeep",
    tint: "bg-lavender text-[#7d6ec6]",
  },
];

export default function WorkspaceNav() {
  const pathname = usePathname();
  return (
    <aside className="p-2 md:p-3">
      <div className="text-[11px] tracking-[0.2em] font-semibold text-inkSubtle px-3 pt-2 pb-3">TOOLS</div>
      <nav className="space-y-1.5">
        {tools.map((t) => {
          const active = pathname?.startsWith(t.href);
          const Icon = t.icon;
          return (
            <Link
              key={t.href}
              href={t.href}
              className={`flex items-start gap-3 px-3 py-2.5 rounded-xl transition ${
                active ? "bg-cream/60 border border-line shadow-sm" : "hover:bg-canvas"
              }`}
            >
              <div className={`mt-0.5 h-8 w-8 rounded-lg grid place-items-center shrink-0 ${t.tint}`}>
                <Icon size={15} />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${t.dot}`} />
                  <span className="text-sm font-medium text-ink truncate">{t.name}</span>
                </div>
                <div className="mt-0.5 text-[11px] text-inkSubtle truncate">{t.hint}</div>
              </div>
            </Link>
          );
        })}
      </nav>
      <div className="mt-8 rounded-xl border border-line bg-canvas/60 p-3 text-[11px] text-inkSubtle">
        <div className="font-semibold text-ink">What's in the archive</div>
        <div className="mt-1.5">3,208 chunks · 109.8 h · 170 videos</div>
      </div>
    </aside>
  );
}
