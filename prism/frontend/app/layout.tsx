import type { Metadata } from "next";
import "./globals.css";
import OfflineBanner from "@/components/ui/OfflineBanner";
import { ThemeProvider } from "@/lib/theme";

export const metadata: Metadata = {
  title: "PRISM — Clinical Dashboard",
  description: "Passive Readings → Intelligent Scalable Medicine. AI-powered multimodal diagnostic platform for underserved populations.",
  keywords: ["PRISM", "AI diagnostics", "healthcare", "ABDM", "federated learning"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Prevent flash of wrong theme on load */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var t = localStorage.getItem('prism_theme');
                  if (t === 'dark' || (!t && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                    document.documentElement.classList.add('dark');
                  }
                } catch(e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-screen bg-[#f0f4f8] dark:bg-[#0a0f1e] text-slate-800 dark:text-slate-100 antialiased transition-colors duration-200">
        <ThemeProvider>
          <OfflineBanner />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
