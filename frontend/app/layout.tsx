import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CORE — Cognitive Operations & Reliability Engine",
  description:
    "Nine AI agents over a unified knowledge base + RAG: ingests APQP and QMS documents across parts, detects quality gaps, runs RCA, and answers with citations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
