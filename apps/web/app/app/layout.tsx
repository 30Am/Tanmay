import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import WorkspaceNav from "@/components/workspace/WorkspaceNav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-soft">
      <header className="sticky top-0 z-20 bg-white/75 backdrop-blur-md border-b border-line">
        <div className="wrap h-16 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2 text-sm text-inkMuted hover:text-ink transition">
              <ArrowLeft size={16} />
              <span>Home</span>
            </Link>
            <div className="hidden md:flex items-center gap-2">
              <span className="h-6 w-6 rounded-full bg-gradient-to-br from-pink to-lavender" />
              <span className="font-semibold tracking-tight text-sm">Create with Tanmay</span>
            </div>
          </div>
          <div className="text-[11px] text-inkSubtle font-mono">workspace · beta</div>
        </div>
      </header>

      <div className="wrap py-8">
        <div className="workspace-card p-4 md:p-5 grid md:grid-cols-[240px_1fr] gap-5 min-h-[70vh]">
          <WorkspaceNav />
          <div>{children}</div>
        </div>
      </div>
    </div>
  );
}
