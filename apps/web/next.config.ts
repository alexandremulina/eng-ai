import type { NextConfig } from "next"
import withPWA from "@ducanh2912/next-pwa"
import createNextIntlPlugin from "next-intl/plugin"

const withNextIntl = createNextIntlPlugin("./i18n/request.ts")

const withPWAConfig = withPWA({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  register: true,
  cacheOnFrontEndNav: true,
  aggressiveFrontEndNavCaching: true,
  reloadOnOnline: true,
  workboxOptions: {
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/.*\.supabase\.co\/.*/i,
        handler: "NetworkFirst",
        options: {
          cacheName: "supabase-cache",
          expiration: { maxAgeSeconds: 60 * 60 },
        },
      },
    ],
  },
})

const nextConfig: NextConfig = {}

export default withNextIntl(withPWAConfig(nextConfig))
