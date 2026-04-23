import { cn } from "@/lib/utils";

export default function Logo({
  size = "md",
  className,
  showWordmark = true,
}: {
  size?: "sm" | "md" | "lg";
  className?: string;
  showWordmark?: boolean;
}) {
  const dim = { sm: "h-7 w-7", md: "h-8 w-8", lg: "h-9 w-9" }[size];
  const textSize = { sm: "text-[14px]", md: "text-[15px]", lg: "text-[22px]" }[size];
  return (
    <div className={cn("inline-flex items-center gap-2.5", className)}>
      <span className={cn("rounded-[10px] bg-gradient-sunrise", dim)} aria-hidden />
      {showWordmark && <span className={cn("font-semibold tracking-tight", textSize)}>Tanmay</span>}
    </div>
  );
}
