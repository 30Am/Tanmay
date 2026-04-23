"use client";

import { useEffect, useRef, useState } from "react";

interface Props {
  target: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  /** Passed as-is, no separators. For display with commas, set format="commas". */
  format?: "commas" | "plain";
  className?: string;
}

/** Counts from 0 to `target` when it first enters viewport. */
export default function CountUp({
  target,
  duration = 1600,
  prefix = "",
  suffix = "",
  format = "commas",
  className,
}: Props) {
  const ref = useRef<HTMLSpanElement>(null);
  const [value, setValue] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      setValue(target);
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting && !started.current) {
            started.current = true;
            const start = performance.now();
            const tick = (now: number) => {
              const t = Math.min(1, (now - start) / duration);
              // ease-out cubic
              const eased = 1 - Math.pow(1 - t, 3);
              setValue(Math.floor(target * eased));
              if (t < 1) requestAnimationFrame(tick);
              else setValue(target);
            };
            requestAnimationFrame(tick);
            obs.disconnect();
          }
        }
      },
      { threshold: 0.4 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [target, duration]);

  const display = format === "commas" ? value.toLocaleString("en-IN") : String(value);
  return (
    <span ref={ref} className={className}>
      {prefix}
      {display}
      {suffix}
    </span>
  );
}
