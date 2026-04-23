"use client";

import { useEffect, useRef, useState } from "react";
import { useSession, signOut } from "next-auth/react";
import { LogOut, Settings } from "lucide-react";

function initials(name?: string | null, email?: string | null): string {
  const src = (name ?? email ?? "User").trim();
  const parts = src.split(/\s+/);
  if (parts.length >= 2) return (parts[0]![0]! + parts[1]![0]!).toUpperCase();
  return src.slice(0, 2).toUpperCase();
}

export default function UserMenu() {
  const { data: session, status } = useSession();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!ref.current || ref.current.contains(e.target as Node)) return;
      setOpen(false);
    }
    if (open) document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  const name = session?.user?.name ?? "Signed out";
  const email = session?.user?.email ?? "";
  const plan = session?.user?.plan ?? "Pro";

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full card-flat flex items-center gap-3 p-3 hover:bg-surface/70 transition"
      >
        <span
          className="h-10 w-10 rounded-full bg-gradient-sunrise shrink-0 grid place-items-center text-[13px] font-semibold text-ink"
          aria-hidden
        >
          {status === "authenticated" ? initials(name, email) : "··"}
        </span>
        <div className="min-w-0 text-left">
          <div className="text-[14px] font-semibold text-ink truncate leading-tight">{name}</div>
          <div className="text-[12px] text-ink-3 mt-0.5 truncate">
            {status === "authenticated" ? plan : "Sign in"}
          </div>
        </div>
      </button>

      {open && status === "authenticated" && (
        <div className="absolute bottom-full left-0 right-0 mb-2 card p-2 z-50">
          <div className="px-3 py-2 border-b border-border mb-1">
            <div className="text-[13px] font-semibold text-ink truncate">{name}</div>
            <div className="text-[12px] text-ink-3 truncate">{email}</div>
          </div>
          <a
            href="#"
            className="flex items-center gap-2.5 w-full rounded-lg px-3 py-2 text-[13px] text-ink-2 hover:bg-bg transition"
          >
            <Settings size={14} /> Settings
          </a>
          <button
            onClick={() => signOut({ callbackUrl: "/" })}
            className="flex items-center gap-2.5 w-full rounded-lg px-3 py-2 text-[13px] text-coral-deep hover:bg-coral/10 transition"
          >
            <LogOut size={14} /> Sign out
          </button>
        </div>
      )}
    </div>
  );
}
