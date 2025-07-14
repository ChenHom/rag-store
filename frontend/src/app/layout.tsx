import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RAG Store",
  description: "Query your documents",
};

function NavBar() {
  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between">
        <Link href="/" className="font-bold text-xl">
          RAG Store
        </Link>
        <div className="space-x-4">
          <Link href="/chat" className="hover:text-gray-300">
            💬 聊天
          </Link>
          <Link href="/search" className="hover:text-gray-300">
            🔍 進階搜尋
          </Link>
          <Link href="/upload" className="hover:text-gray-300">
            📤 上傳
          </Link>
          <Link href="/classification" className="hover:text-gray-300">
            📁 分類管理
          </Link>
          <Link href="/timeseries" className="hover:text-gray-300">
            📈 時間序列
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <NavBar />
        <main>{children}</main>
      </body>
    </html>
  );
}
