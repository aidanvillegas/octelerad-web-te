"use client";

import * as React from "react";
import clsx from "clsx";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
};

export const Button = React.forwardRef<HTMLButtonElement, Props>(function Button(
  { className, variant = "secondary", size = "md", loading = false, disabled, children, ...rest },
  ref
) {
  const base =
    "inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-sky-500 ring-offset-neutral-950 disabled:opacity-50 disabled:pointer-events-none";
  const sizes = { sm: "h-8 px-3 text-sm", md: "h-10 px-4", lg: "h-12 px-6 text-base" } as const;
  const variants = {
    primary: "bg-white text-black hover:bg-neutral-200",
    secondary: "bg-neutral-800 text-neutral-100 hover:bg-neutral-700",
    ghost: "bg-transparent text-neutral-100 hover:bg-neutral-800",
    danger: "bg-red-600 text-white hover:bg-red-500",
  } as const;

  return (
    <button
      ref={ref}
      className={clsx(base, sizes[size], variants[variant], className)}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && (
        <svg className="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
      )}
      {children}
    </button>
  );
});
