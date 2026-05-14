import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PRISM — Clinical Dashboard",
  description: "Passive Readings → Intelligent Scalable Medicine. AI-powered multimodal diagnostic platform for underserved populations.",
  keywords: ["PRISM", "AI diagnostics", "healthcare", "ABDM", "federated learning"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0a0f1e] text-[#f8fafc] antialiased">
        {children}
      </body>
    </html>
  );
}
