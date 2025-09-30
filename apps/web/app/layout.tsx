import "./globals.css";
import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "Datasets",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-neutral-950 text-neutral-100">
        {children}
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: "#0b0f1a",
              color: "#fff",
              border: "1px solid #2a2f3a",
            },
          }}
        />
      </body>
    </html>
  );
}
