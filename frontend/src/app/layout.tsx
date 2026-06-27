import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import "./globals.css"
import { Providers } from "@/lib/providers"
import { Sidebar } from "@/components/layout/sidebar"
import { Header } from "@/components/layout/header"
import { PageContainer } from "@/components/layout/page-container"

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] })
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] })

export const metadata: Metadata = {
  title: "HearMe AI — Intelligent Knowledge Platform",
  description: "AI-powered chatbot with sentiment analysis, knowledge reasoning, and long-term memory",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="min-h-full">
        <Providers>
          <Sidebar />
          <div className="flex min-h-screen flex-col">
            <Header />
            <PageContainer>{children}</PageContainer>
          </div>
        </Providers>
      </body>
    </html>
  )
}
