"use client";

import * as React from "react";
import clsx from "clsx";

type DropzoneProps = {
  onFile: (file: File) => void;
};

export function Dropzone({ onFile }: DropzoneProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = React.useState(false);

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0];
    if (file) {
      onFile(file);
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Choose file to import"
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      onClick={() => inputRef.current?.click()}
      onDragOver={(event) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragActive(false);
        handleFiles(event.dataTransfer.files);
      }}
      className={clsx(
        "flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed p-6 text-center transition-colors",
        dragActive ? "border-sky-400 bg-sky-950/20" : "border-neutral-700 hover:bg-neutral-800/40"
      )}
    >
      <p className="font-medium">Drop CSV or JSON here</p>
      <p className="mt-1 text-sm opacity-70">or click to choose a file</p>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.json,application/json,text/csv"
        className="hidden"
        onChange={(event) => handleFiles(event.target.files)}
      />
    </div>
  );
}
