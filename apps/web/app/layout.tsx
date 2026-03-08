import type { Metadata, Viewport } from "next"
import { Inter } from "next/font/google"
import { NextIntlClientProvider } from "next-intl"
import { getLocale, getMessages } from "next-intl/server"
import "./globals.css"
import { ThemeProvider } from "@/components/ThemeProvider"
import { Toaster } from "sonner"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "EngBrain",
  description: "Engineering tools for pump specialists",
  manifest: "/manifest.json",
}

export const viewport: Viewport = {
  themeColor: "#0066FF",
  width: "device-width",
  initialScale: 1,
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = await getLocale()
  const messages = await getMessages()
  return (
    <html lang={locale} suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <NextIntlClientProvider locale={locale} messages={messages}>
            {children}
            <Toaster richColors position="top-center" />
          </NextIntlClientProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
