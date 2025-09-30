import * as React from "react";
import clsx from "clsx";

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={clsx("rounded-lg border border-neutral-800 bg-neutral-900/50 p-4", className)}>{children}</div>;
}

export function CardHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-3">
      <h3 className="text-lg font-semibold">{title}</h3>
      {subtitle && <p className="text-sm opacity-70">{subtitle}</p>}
    </div>
  );
}
