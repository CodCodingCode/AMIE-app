import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { EhrProvider } from "./contexts/EhrContext";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Bluebox",
  icons: {
    icon: "/reallogo.png",
  },
  description: "Get instant, reliable medical guidance anytime, anywhere with Bluebox",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={`${inter.variable} font-sans antialiased`}>
        <EhrProvider>
          {children}
        </EhrProvider>
      </body>
    </html>
  );
}