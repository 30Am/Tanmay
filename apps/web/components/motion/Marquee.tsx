"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Infinite horizontal marquee. Duplicates children once so the CSS -50% translate loops
 * seamlessly. Pauses on hover.
 */
export default function Marquee({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("marquee", className)}>
      <div className="marquee-track">
        {children}
        {children}
      </div>
    </div>
  );
}
