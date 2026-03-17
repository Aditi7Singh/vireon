import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Vireon - AI Financial Copilot",
  description: "Intelligent financial monitoring, anomaly detection, and CFO-grade insights for startups",
  icons: {
    icon: "/logo.svg",
    apple: "/logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
