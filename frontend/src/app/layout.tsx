import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { PersonaProvider } from "@/lib/persona-context";
import { Nav } from "@/components/Nav";
import { SponsorsStrip } from "@/components/SponsorsStrip";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Wingmate",
  description: "Your AI agent goes on the pre-date so you only go on the good ones.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f3f5f9" },
    { media: "(prefers-color-scheme: dark)", color: "#0b0f17" },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} min-h-dvh font-sans antialiased`}>
        <PersonaProvider>
          <Nav />
          <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10">{children}</main>
          <SponsorsStrip />
        </PersonaProvider>
      </body>
    </html>
  );
}
