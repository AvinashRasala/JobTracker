import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/cn";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
}

const variants = {
  primary: "bg-ledger text-white hover:bg-ledger-light",
  secondary: "bg-white text-ink border border-hairline hover:bg-paper",
  ghost: "text-ink-soft hover:text-ink hover:bg-paper",
  danger: "bg-stamp-red text-white hover:opacity-90",
};

const sizes = {
  sm: "text-xs px-3 py-1.5",
  md: "text-sm px-4 py-2",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors disabled:opacity-50 disabled:pointer-events-none",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
