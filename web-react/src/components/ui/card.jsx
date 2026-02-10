import { cn } from "../../lib/utils";

export function Card({ className, ...props }) {
  return (
    <div
      className={cn(
        `
        rounded-2xl
        border border-slate-200/70
        bg-white/70
        backdrop-blur
        shadow-sm
        transition-shadow
        hover:shadow-md
        dark:border-slate-700/60
        dark:bg-slate-900/60
        `,
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }) {
  return (
    <div
      className={cn("flex flex-col gap-1 p-4", className)}
      {...props}
    />
  );
}

export function CardTitle({ className, ...props }) {
  return (
    <h3
      className={cn(
        "text-sm font-semibold uppercase tracking-wide text-slate-900 dark:text-white",
        className
      )}
      {...props}
    />
  );
}

export function CardDescription({ className, ...props }) {
  return (
    <p
      className={cn(
        "text-sm leading-relaxed text-slate-600 dark:text-slate-300",
        className
      )}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }) {
  return (
    <div
      className={cn("p-4 pt-0", className)}
      {...props}
    />
  );
}
