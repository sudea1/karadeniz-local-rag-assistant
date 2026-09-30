"use client"

import { Mountain, Sparkles } from "lucide-react"

export function SiteHeader() {
  return (
    <header className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="glass flex size-11 items-center justify-center rounded-2xl border border-white/15 shadow-lg shadow-black/30">
          <Mountain className="size-5 text-primary" aria-hidden="true" />
        </div>
        <div className="leading-tight">
          <p className="text-base font-bold tracking-tight text-white sm:text-lg">Karadeniz Gezi Asistanı</p>
          <p className="hidden text-xs text-white/60 sm:block">Yerel rehberin cebinde</p>
        </div>
      </div>

      <div className="glass flex items-center gap-2 rounded-full border border-white/15 px-3.5 py-2 shadow-lg shadow-black/30">
        <Sparkles className="size-3.5 text-accent" aria-hidden="true" />
        <span className="text-xs font-medium text-white/85">Yapay Zekâ Destekli Yerel Rehber</span>
      </div>
    </header>
  )
}
