import type { ReactNode } from "react";

export function Card({
  title,
  description,
  children,
  className = "",
}: {
  title?: string;
  description?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-xl border border-white/10 bg-surface-raised p-5 shadow-sm ${className}`}
    >
      {title && <h3 className="text-sm font-medium uppercase tracking-wide text-slate-400">{title}</h3>}
      {description && <p className="mt-1 text-xs text-slate-500">{description}</p>}
      <div className={title || description ? "mt-4" : undefined}>{children}</div>
    </section>
  );
}
