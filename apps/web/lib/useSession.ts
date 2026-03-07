"use client"
import { useEffect, useState } from "react"
import { createClient } from "./supabase"
import type { Session } from "@supabase/supabase-js"

export function useSession() {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const supabase = createClient()
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setLoading(false)
    })
    const { data: listener } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s)
    })
    return () => listener.subscription.unsubscribe()
  }, [])

  return {
    session,
    loading,
    token: session?.access_token ?? null,
    user: session?.user ?? null,
  }
}
