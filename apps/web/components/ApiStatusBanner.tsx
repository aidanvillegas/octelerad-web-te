"use client";

import { useEffect, useState } from "react";

import { http } from "@/lib/api";

export default function ApiStatusBanner() {
  const [ok, setOk] = useState(true);

  useEffect(() => {
    async function ping() {
      try {
        await http.get("/healthz");
        setOk(true);
      } catch {
        setOk(false);
      }
    }

    ping();
  }, []);

  if (ok) return null;

  return (
    <div className="mb-4 rounded-md border border-red-700 bg-red-900/30 p-3 text-sm">
      Cannot reach API. Check <code>NEXT_PUBLIC_API_URL</code> and CORS. Open console/network for details.
    </div>
  );
}
