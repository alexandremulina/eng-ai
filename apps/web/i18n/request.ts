import { getRequestConfig } from "next-intl/server"
import { cookies } from "next/headers"

export default getRequestConfig(async () => {
  const cookieStore = await cookies()
  const locale = cookieStore.get("locale")?.value ?? "en"
  const validLocales = ["en", "pt", "es"]
  const safeLocale = validLocales.includes(locale) ? locale : "en"

  const messages = (await import(`./${safeLocale}.json`)).default
  return { locale: safeLocale, messages }
})
