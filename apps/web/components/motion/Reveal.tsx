"use client";

import { createElement, useEffect, useRef, useState, type ElementType, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Props {
  children: ReactNode;
  as?: ElementType;
  delay?: 0 | 1 | 2 | 3 | 4 | 5 | 6;
  once?: boolean;
  className?: string;
}

/**
 * Fades the wrapped element up 14px on first viewport entry. Uses IntersectionObserver
 * so the browser does the work; animation is pure CSS (see `.reveal` in globals.css).
 */
export default function Reveal({ children, as = "div", delay = 0, once = true, className }: Props) {
  const ref = useRef<HTMLElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setVisible(true);
            if (once) obs.disconnect();
          } else if (!once) {
            setVisible(false);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [once]);

  return createElement(
    as,
    {
      ref,
      className: cn(
        "reveal",
        visible && "in-view",
        delay > 0 && `reveal-delay-${delay}`,
        className,
      ),
    },
    children,
  );
}
