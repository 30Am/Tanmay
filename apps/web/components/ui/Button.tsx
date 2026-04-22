import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className, ...props }, ref) => {
    const base =
      "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50";
    const styles =
      variant === "primary"
        ? "bg-accent text-[#0f1115] hover:brightness-110"
        : "border border-border bg-panel text-white hover:border-accent";
    return <button ref={ref} className={cn(base, styles, className)} {...props} />;
  },
);

Button.displayName = "Button";
