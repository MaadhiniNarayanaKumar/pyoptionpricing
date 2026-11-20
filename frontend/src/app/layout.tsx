import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const title = "pyoptionpricing | Option pricing and Greeks calculator";
const description =
  "Price European, American, Asian and barrier options with Black-Scholes, a binomial tree and Monte Carlo. Compare models, see Greeks, payoffs, convergence and the implied volatility smile.";

export const metadata: Metadata = {
  // Absolute base for the share image. Change this to the custom domain once it is final.
  metadataBase: new URL("https://pyoptionpricingui.vercel.app"),
  title,
  description,
  openGraph: { title, description, type: "website", siteName: "pyoptionpricing" },
  twitter: { card: "summary_large_image", title, description },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-100">{children}</body>
    </html>
  );
}
