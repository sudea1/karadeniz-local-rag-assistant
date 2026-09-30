"use client"

import { MapPin } from "lucide-react"
import { cities, type City } from "@/lib/cities"
import { cn } from "@/lib/utils"

type Props = {
  active: City
  onSelect: (city: City) => void
}

export function CitySelector({ active, onSelect }: Props) {
  return (
    <nav aria-label="Şehir seçimi" className="relative z-30 w-full">
      <div className="glass mx-auto flex w-full max-w-full items-center gap-1.5 overflow-x-auto rounded-full border border-white/10 p-1.5 shadow-2xl shadow-black/40 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {cities.map((city) => {
          const isActive = city.id === active.id
          return (
            <button
              key={city.id}
              type="button"
              onClick={() => onSelect(city)}
              aria-pressed={isActive}
              className={cn(
                "group relative flex shrink-0 cursor-pointer items-center gap-1.5 rounded-full px-4 py-2.5 text-sm font-semibold transition-all duration-300 outline-none focus-visible:ring-2 focus-visible:ring-primary/70",
                isActive
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30"
                  : "text-foreground/70 hover:bg-white/10 hover:text-foreground",
              )}
            >
              <MapPin
                className={cn(
                  "size-3.5 transition-transform duration-300",
                  isActive ? "scale-110" : "text-primary/80 group-hover:scale-110",
                )}
              />
              {city.name}
            </button>
          )
        })}
      </div>
    </nav>
  )
}