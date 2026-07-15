import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

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
      <body className={`${inter.className} min-h-full flex flex-col bg-slate-950 text-slate-100`}>
        {children}
      </body>
    </html>
  );
}
