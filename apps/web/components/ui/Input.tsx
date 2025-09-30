"use client";

import * as React from "react";
import clsx from "clsx";

type Props = React.InputHTMLAttributes<HTMLInputElement> & { label?: string; helperText?: string };

export const Input = React.forwardRef<HTMLInputElement, Props>(function Input(
  { label, helperText, className, ...rest },
  ref
) {
  return (
    <label className="block">
      {label && <div className="mb-1 text-sm">{label}</div>}
      <input
        ref={ref}
        className={clsx(
          "w-full rounded-md border border-neutral-700 bg-white text-neutral-900 px-3 py-2 placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-sky-500",
          className
        )}
        {...rest}
      />
      {helperText && <div className="mt-1 text-xs opacity-70">{helperText}</div>}
    </label>
  );
});
