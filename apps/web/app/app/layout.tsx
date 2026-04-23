import Sidebar from "@/components/workspace/Sidebar";
import Topbar from "@/components/workspace/Topbar";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
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
