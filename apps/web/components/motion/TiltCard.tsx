"use client";

import { useRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * TiltCard — rotates its child element slightly based on mouse position within its bounds.
 * Resting rotation is configurable so the existing polaroid tilt stays applied.
 */
interface Props {
  children: ReactNode;
  className?: string;
  /** Max X rotation in degrees. */
  maxTiltX?: number;
  /** Max Y rotation in degrees. */
  maxTiltY?: number;
  /** Resting angle (deg) the element returns to when idle. */
  restingRotation?: number;
}

export default function TiltCard({
  children,
  className,
  maxTiltX = 6,
  maxTiltY = 6,
  restingRotation = 0,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);

  function onMove(e: React.MouseEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width - 0.5; // -0.5 .. 0.5
    const ny = (e.clientY - rect.top) / rect.height - 0.5;
    const rx = (-ny * maxTiltX * 2).toFixed(2);
    const ry = (nx * maxTiltY * 2).toFixed(2);
    el.style.transform = `perspective(900px) rotate(${restingRotation}deg) rotateX(${rx}deg) rotateY(${ry}deg) scale(1.02)`;
  }

  function onLeave() {
    const el = ref.current;
    if (!el) return;
    el.style.transform = `rotate(${restingRotation}deg)`;
  }

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className={cn("transition-transform duration-300 ease-out", className)}
      style={{ transform: `rotate(${restingRotation}deg)` }}
    >
      {children}
    </div>
  );
}
