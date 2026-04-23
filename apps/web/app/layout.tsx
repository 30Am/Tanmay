import type { Metadata } from "next";
import { Fraunces, Inter } from "next/font/google";
import "./globals.css";
import ScrollProgress from "@/components/motion/ScrollProgress";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  style: ["normal", "italic"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Create with Tanmay",
  description:
    "Three creator tools trained on ten years of podcasts, posts, PUBG streams, stage bits, and late-night WhatsApp takes. You bring the idea, we bring the voice that built AIB.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable}`}>
      <body className="font-sans antialiased">
        <ScrollProgress />
        <div className="asterisk-note select-none">✻</div>
        {children}
      </body>
    </html>
  );
}
