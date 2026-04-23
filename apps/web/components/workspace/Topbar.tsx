import { Bell, Search, Settings } from "lucide-react";

export default function Topbar() {
  return (
    <div className="flex items-center justify-between px-12 py-6 gap-6">
      <label className="relative flex-1 max-w-[420px]">
        <Search size={15} className="absolute left-5 top-1/2 -translate-y-1/2 text-ink-3" />
        <input
          type="search"
          placeholder="Search ideas, history, or templates…"
          className="w-full rounded-pill bg-surface border border-border pl-11 pr-4 py-3 text-[14px] text-ink placeholder:text-ink-3 outline-none focus:border-ink/30 transition"
        />
      </label>
      <div className="flex items-center gap-2">
        <span className="hidden md:inline-flex items-center rounded-lg border border-border bg-surface px-2.5 py-1.5 text-[12px] font-mono text-ink-2">⌘ K</span>
        <button className="h-10 w-10 rounded-full border border-border bg-surface grid place-items-center text-ink-2 hover:bg-bg transition" aria-label="Notifications">
          <Bell size={16} />
        </button>
        <button className="h-10 w-10 rounded-full border border-border bg-surface grid place-items-center text-ink-2 hover:bg-bg transition" aria-label="Settings">
          <Settings size={16} />
        </button>
      </div>
    </div>
  );
}
