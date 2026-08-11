import type { Metadata } from "next";
import "./globals.css";
import AuthGuard from "@/components/AuthGuard";

export const metadata: Metadata = {
  title: "AuthentiCite - Academic Paper Rewriter & Similarity Analyzer",
  description: "Detect similarity, rewrite academic text, and format automatically into IEEE/Springer templates.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <body className="font-sans min-h-full flex flex-col bg-slate-950 text-slate-100">
        <AuthGuard>{children}</AuthGuard>
      </body>
    </html>
  );
}
