import Link from "next/link";
import { AlignLeft, Box, MessageSquare } from "lucide-react";

export default function WorkspaceHome() {
  const tiles = [
    { href: "/app/content", title: "Content Generation", desc: "Drop an idea, get a Tanmay-voice script + description + rationale, cited.", icon: AlignLeft, bg: "bg-salmon/20 text-salmon" },
    { href: "/app/ad", title: "Ad Generation", desc: "Structured brief in, schema-validated ad out, with brand-safety + duration checks.", icon: Box, bg: "bg-sky text-[#3a7ab0]" },
    { href: "/app/qa", title: "How Would Tanmay Answer", desc: "Ask anything. Multi-query retrieval + citation verifier decide if he's spoken on it.", icon: MessageSquare, bg: "bg-lavender text-[#7d6ec6]" },
  ];
  return (
    <div className="p-6 md:p-10">
      <h1 className="font-serif text-3xl tracking-tight">Pick a tool.</h1>
      <p className="mt-2 text-inkMuted max-w-lg">
        Three tools, one brain with good timing. Each reads ten years of Tanmay before it writes a line.
      </p>
      <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {tiles.map((t) => {
          const Icon = t.icon;
          return (
            <Link key={t.href} href={t.href} className="card p-5 group hover:shadow-softLg transition">
              <div className={`h-10 w-10 rounded-xl grid place-items-center ${t.bg}`}>
                <Icon size={18} />
              </div>
              <div className="mt-4 font-semibold">{t.title}</div>
              <div className="mt-1 text-sm text-inkMuted">{t.desc}</div>
              <div className="mt-4 text-sm text-pinkDeep opacity-0 group-hover:opacity-100 transition">Open →</div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
