import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { AuthProvider } from "@/lib/auth-context";

const display = Space_Grotesk({ subsets: ["latin"], variable: "--font-display", weight: ["500", "700"] });
const body = IBM_Plex_Sans({ subsets: ["latin"], variable: "--font-body", weight: ["400", "500", "600"] });
const dataFont = IBM_Plex_Mono({ subsets: ["latin"], variable: "--font-data", weight: ["400", "500"] });

export const metadata: Metadata = {
  title: "JobTrack AI",
  description: "Automatically track every job application, across every platform.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${dataFont.variable}`}>
      <body className="font-body">
        <QueryProvider>
          <AuthProvider>{children}</AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
