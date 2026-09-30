"use client"

import { useState } from "react"
import Image from "next/image"
import { Compass, MessageCircle } from "lucide-react"
import { cities, type City } from "@/lib/cities"
import { CitySelector } from "@/components/city-selector"
import { SiteHeader } from "@/components/site-header"
import { TravelAssistant } from "@/components/travel-assistant"

export default function Page() {
  const [active, setActive] = useState<City>(cities[0])
  const [chatOpen, setChatOpen] = useState(false)

  return (
    <main className="relative min-h-svh w-full overflow-hidden text-white">
      {/* dynamic backgrounds */}
      <div className="pointer-events-none fixed inset-0 -z-10">         {cities.map((city) => (
          <div
            key={city.id}
            className="absolute inset-0 transition-opacity duration-[1200ms] ease-out"
            style={{ opacity: city.id === active.id ? 1 : 0 }}
            aria-hidden={city.id !== active.id}
          >
            <Image
              src={city.image || "/placeholder.svg"}
              alt={`${city.name} — ${city.spot}`}
              fill
              priority={city.id === cities[0].id}
              sizes="100vw"
              className="object-cover"
            />
          </div>
        ))}
        {/* overlays for depth + legibility */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#04140f]/70 via-[#04140f]/25 to-[#04140f]/90" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#04140f]/60 via-transparent to-transparent" />
      </div>

      <div className="mx-auto flex min-h-svh w-full max-w-6xl flex-col px-4 py-5 sm:px-6 sm:py-6">
        <SiteHeader />

        {/* hero */}
        <section className="flex flex-1 flex-col justify-center py-10">
          <div className="max-w-2xl">
            <div key={active.id} className="animate-rise">
              <span className="glass inline-flex items-center gap-2 rounded-full border border-white/15 px-3.5 py-1.5 text-xs font-medium text-white/80">
                <Compass className="size-3.5 text-accent" aria-hidden="true" />
                {active.name} · {active.spot}
              </span>
            </div>

            <h1 className="mt-5 text-balance text-5xl font-black leading-[0.95] tracking-tight drop-shadow-2xl sm:text-7xl md:text-8xl">
              KARADENİZ&apos;İ
              <span className="block bg-gradient-to-r from-emerald-300 via-emerald-100 to-accent bg-clip-text text-transparent">
                KEŞFET
              </span>
            </h1>

            <p key={`${active.id}-tag`} className="animate-rise mt-5 max-w-lg text-pretty text-base text-white/75 sm:text-lg">
              {active.tagline}. Yapay zekâ destekli yerel rehberinle rotanı planla, yöresel lezzetleri keşfet ve
              yaylalara doğru yola çık.
            </p>
          </div>
        </section>

        {/* city selector pinned above the fold's bottom */}
        <section className="pb-4 lg:pr-[26rem]">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-white/50">Bir şehir seç</p>
          <CitySelector active={active} onSelect={setActive} />
        </section>
      </div>

      {/* embedded chat — desktop */}
      <div className="pointer-events-none fixed bottom-6 right-6 z-30 hidden w-[24rem] lg:block">
        <div className="pointer-events-auto">
          <TravelAssistant city={active} />
        </div>
      </div>

      {/* chat drawer — mobile / tablet */}
      {chatOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Kapat"
            onClick={() => setChatOpen(false)}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          <div className="absolute inset-x-3 bottom-3 animate-rise">
            <TravelAssistant city={active} onClose={() => setChatOpen(false)} />
          </div>
        </div>
      )}

      {/* floating chat toggle — mobile */}
      {!chatOpen && (
        <button
          type="button"
          onClick={() => setChatOpen(true)}
          aria-label="Asistanı aç"
          className="fixed bottom-5 right-5 z-30 flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-2xl shadow-primary/40 transition hover:brightness-110 lg:hidden"
        >
          <MessageCircle className="size-6" aria-hidden="true" />
        </button>
      )}
    </main>
  )
}
