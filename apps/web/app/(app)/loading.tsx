export default function AppLoading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4" aria-live="polite" aria-busy="true">
      <div className="flex flex-col items-center gap-3">
        <div
          className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-blue-500"
          aria-hidden
        />
        <p className="text-sm text-white/60">Loading…</p>
      </div>
    </div>
  )
}
