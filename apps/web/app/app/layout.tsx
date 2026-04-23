"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/workspace/Sidebar";
import Topbar from "@/components/workspace/Topbar";
import IconSidebar from "@/components/workspace/IconSidebar";
import TabSwitcher from "@/components/workspace/TabSwitcher";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isTool =
    pathname === "/app/content" ||
    pathname === "/app/ads" ||
    pathname === "/app/qa" ||
    pathname?.startsWith("/app/content/") ||
    pathname?.startsWith("/app/ads/") ||
    pathname?.startsWith("/app/qa/");

  if (isTool) {
    return (
      <div className="flex min-h-screen bg-bg">
        <IconSidebar />
        <main className="flex-1 min-w-0 px-10 pb-20">{children}</main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar />
      <main className="flex-1 min-w-0">
        <Topbar />
        <div className="px-12 pb-20">{children}</div>
      </main>
    </div>
  );
}

export { TabSwitcher };
