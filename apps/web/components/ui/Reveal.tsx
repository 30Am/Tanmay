"use client";

import { createElement, useEffect, useRef, useState, type ElementType, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Props {
  children: ReactNode;
  as?: ElementType;
  delay?: 0 | 1 | 2 | 3 | 4 | 5 | 6;
  className?: string;
}

/** Fade-up on first viewport entry. Pure CSS via .reveal / .in-view classes. */
export default function Reveal({ children, as = "div", delay = 0, className }: Props) {
  const ref = useRef<HTMLElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setVisible(true);
            obs.disconnect();
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return createElement(
    as,
    {
      ref,
      className: cn("reveal", visible && "in-view", delay > 0 && `reveal-d${delay}`, className),
    },
    children,
  );
}
