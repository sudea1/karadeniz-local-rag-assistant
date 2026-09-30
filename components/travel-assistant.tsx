"use client"

import { useEffect, useRef, useState } from "react"
import { ArrowUp, Bot, MapPin, Mic, Sparkles, X } from "lucide-react"
import type { City } from "@/lib/cities"
import { cn } from "@/lib/utils"

// Yerel FastAPI backend
const API_URL = "http://127.0.0.1:8000/sohbet"

type Place = {
  yer_adi: string
  il: string
  harita_linki: string
  foto?: string
}

type Message = {
  id: string
  role: "user" | "assistant"
  text: string
  places?: Place[]
}

const suggestions = [
  "3 Günlük Rize Rotası",
  "Trabzon'da Ne Yenir?",
  "En Güzel Yaylalar",
]

type Props = {
  city: City
  onClose?: () => void
}

export function TravelAssistant({ city, onClose }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [typing, setTyping] = useState(false)

  const scrollRef = useRef<HTMLDivElement>(null)
  const composing = useRef(false)

  // Şehir değiştiğinde karşılama mesajını yenile
  useEffect(() => {
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        text: `Merhaba! Ben senin ${city.name} yerel rehberinim. ${city.spot} çevresi, rotalar, lezzetler ve yaylalar hakkında her şeyi sorabilirsin.`,
      },
    ])
  }, [city])

  // Yeni mesaj geldiğinde aşağı kaydır
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    })
  }, [messages, typing])

  async function send(text: string) {
  const trimmed = text.trim()

  if (!trimmed || typing) return

  // ========================================================
  // SOHBET GEÇMİŞİNİ BACKEND FORMATINA ÇEVİR
  // ========================================================

  // Mevcut soruyu messages'a eklemeden ÖNCE geçmişi hazırlıyoruz.
  // Böylece mevcut soru history içinde iki kere gitmez.
  const history = messages
    // Karşılama mesajını RAG hafızasına göndermiyoruz.
    .filter((message) => message.id !== "welcome")
    // Çok fazla geçmiş gönderip modeli şişirmemek için
    // son 10 mesaj yeterli.
    .slice(-10)
    .map((message) => ({
      role: message.role,
      content: message.text,
    }))

  // ========================================================
  // KULLANICI MESAJI
  // ========================================================

  const userMsg: Message = {
    id: crypto.randomUUID(),
    role: "user",
    text: trimmed,
  }

  setMessages((prev) => [...prev, userMsg])

  setInput("")
  setTyping(true)

  try {
    console.log("Soru gönderiliyor:", trimmed)
    console.log("Sohbet geçmişi:", history)

    // ======================================================
    // FASTAPI
    // ======================================================

    const res = await fetch(API_URL, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        message: trimmed,
        history: history,
      }),
    })

    console.log("HTTP durum:", res.status)

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }

    // ======================================================
    // BACKEND CEVABI
    // ======================================================

    const data: {
      answer?: string
      sources?: string[]
      yerler?: Place[]
    } = await res.json()

    console.log("Backend cevabı:", data)

    // ======================================================
    // ASİSTAN MESAJI
    // ======================================================

    const assistantMsg: Message = {
      id: crypto.randomUUID(),
      role: "assistant",

      text:
        data.answer ??
        "Backend cevap döndürdü ancak cevap metni bulunamadı.",

      places: data.yerler,
    }

    setMessages((prev) => [
      ...prev,
      assistantMsg,
    ])
    } catch (err) {
      console.error("Sohbet API hatası:", err)

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text:
            "Sunucudan cevap alınırken bir hata oluştu. Backend'in çalıştığından emin ol.",
        },
      ])
    } finally {
      setTyping(false)
    }
  }

  return (
    <div className="glass flex h-[30rem] w-full flex-col overflow-hidden rounded-3xl border border-white/15 shadow-2xl shadow-black/50">
      {/* HEADER */}
      <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="relative flex size-9 items-center justify-center rounded-xl bg-primary/20 ring-1 ring-primary/40">
            <Bot
              className="size-4.5 text-primary"
              aria-hidden="true"
            />
          </div>

          <div className="leading-tight">
            <p className="text-sm font-semibold text-white">
              Gezi Asistanı
            </p>

            <p className="flex items-center gap-1.5 text-[11px] text-emerald-300">
              <span className="relative flex size-1.5">
                <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex size-1.5 rounded-full bg-emerald-400" />
              </span>

              Yapay Zekâ Aktif · Yerelde çalışıyor
            </p>
          </div>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Sohbeti kapat"
            className="flex size-8 items-center justify-center rounded-full text-white/60 transition hover:bg-white/10 hover:text-white"
          >
            <X className="size-4" />
          </button>
        )}
      </div>

      {/* MESAJLAR */}
      <div
        ref={scrollRef}
        className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
      >
        {messages.map((m) => (
          <div
            key={m.id}
            className={cn(
              "flex animate-msg-in flex-col gap-2",
              m.role === "user"
                ? "items-end"
                : "items-start"
            )}
          >
            <div
              className={cn(
                "max-w-[85%] whitespace-pre-line rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
                m.role === "user"
                  ? "rounded-br-md bg-primary text-primary-foreground shadow-lg shadow-primary/25"
                  : "rounded-bl-md bg-white/10 text-white/90 ring-1 ring-white/10"
              )}
            >
              {m.text}
            </div>

            {/* Backend ileride yer kartları döndürürse hazır */}
            {m.places && m.places.length > 0 && (
              <div className="flex max-w-full flex-wrap gap-2.5">
                {m.places.map((place, i) => (
                  <a
                    key={`${m.id}-${i}`}
                    href={place.harita_linki}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group relative block h-28 w-40 overflow-hidden rounded-2xl shadow-lg shadow-black/40 ring-1 ring-white/10 transition hover:-translate-y-1 hover:shadow-xl"
                  >
                    <img
                      src={
                        place.foto ||
                        `https://picsum.photos/seed/${encodeURIComponent(
                          place.yer_adi
                        )}/300/220`
                      }
                      alt={place.yer_adi}
                      className="size-full object-cover transition duration-500 group-hover:scale-110"
                    />

                    <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent" />

                    <div className="absolute inset-x-0 bottom-0 p-2.5">
                      <p className="text-xs font-bold leading-tight text-white drop-shadow">
                        {place.yer_adi}
                      </p>

                      <p className="mt-0.5 flex items-center gap-1 text-[10px] font-medium text-white/85">
                        <MapPin
                          className="size-2.5"
                          aria-hidden="true"
                        />
                        {place.il}
                      </p>
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* YAZIYOR ANİMASYONU */}
        {typing && (
          <div className="flex animate-msg-in justify-start">
            <div className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-white/10 px-4 py-3 ring-1 ring-white/10">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="size-1.5 rounded-full bg-white/70"
                  style={{
                    animation: "dot-bounce 1.2s infinite",
                    animationDelay: `${i * 0.15}s`,
                  }}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ÖNERİ BUTONLARI */}
      <div className="flex gap-2 overflow-x-auto px-4 pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            disabled={typing}
            onClick={() => send(s)}
            className="flex shrink-0 items-center gap-1.5 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/80 transition hover:border-primary/50 hover:bg-primary/15 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Sparkles
              className="size-3 text-accent"
              aria-hidden="true"
            />
            {s}
          </button>
        ))}
      </div>

      {/* INPUT */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
        className="flex items-center gap-2 border-t border-white/10 p-3"
      >
        <div className="flex flex-1 items-center gap-2 rounded-full border border-white/15 bg-black/20 px-3 py-1.5 focus-within:border-primary/60">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onCompositionStart={() => {
              composing.current = true
            }}
            onCompositionEnd={() => {
              composing.current = false
            }}
            onKeyDown={(e) => {
              if (
                e.key === "Enter" &&
                !e.shiftKey &&
                !composing.current &&
                e.nativeEvent.keyCode !== 229
              ) {
                e.preventDefault()
                send(input)
              }
            }}
            placeholder={`${city.name} hakkında bir şey sor...`}
            aria-label="Mesajınız"
            disabled={typing}
            className="flex-1 bg-transparent text-sm text-white placeholder:text-white/40 outline-none disabled:opacity-60"
          />

          <button
            type="button"
            aria-label="Sesli giriş"
            className="flex size-7 items-center justify-center rounded-full text-white/50 transition hover:bg-white/10 hover:text-white"
          >
            <Mic className="size-4" />
          </button>
        </div>

        <button
          type="submit"
          disabled={!input.trim() || typing}
          aria-label="Gönder"
          className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/30 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ArrowUp className="size-5" />
        </button>
      </form>
    </div>
  )
}