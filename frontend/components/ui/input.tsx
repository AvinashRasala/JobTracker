import { InputHTMLAttributes, forwardRef, LabelHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "w-full rounded-md border border-hairline bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-soft/60 focus:border-ledger focus:outline-none",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";

export function Label(props: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      {...props}
      className={cn("mb-1.5 block text-xs font-medium uppercase tracking-wide text-ink-soft", props.className)}
    />
  );
}
