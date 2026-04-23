import { cn } from "@/lib/utils";

export default function ToolHeader({
  eyebrow,
  title,
  subtitle,
  chipClass,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
  chipClass?: string;
}) {
  return (
    <header className="flex items-start justify-between gap-6 flex-wrap mb-8">
      <div>
        <div className="caption text-coral-deep">{eyebrow}</div>
        <h1 className="mt-3 font-bold tracking-[-0.02em] leading-[1.08] text-[40px] text-ink">{title}</h1>
        <p className="mt-2 text-body text-ink-2 max-w-[540px]">{subtitle}</p>
      </div>
      <span className={cn("chip", chipClass)}>LIVE</span>
    </header>
  );
}
