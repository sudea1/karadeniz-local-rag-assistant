from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag import ask_rag


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Karadeniz Gezi Asistanı API",
    description="Yerel RAG tabanlı Karadeniz gezi asistanı",
    version="2.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ANA SAYFA
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Karadeniz Gezi Asistanı API çalışıyor."
    }


# ============================================================
# SOHBET
# ============================================================

@app.post("/sohbet")
def sohbet(data: dict):

    question = data.get(
        "message",
        ""
    ).strip()

    history = data.get(
        "history",
        []
    )

    if not question:

        return {
            "answer": "Lütfen bir soru yazın.",
            "sources": []
        }

    # Güvenlik / performans için geçmişi sınırla
    if not isinstance(history, list):
        history = []

    history = history[-12:]

    answer, sources = ask_rag(
        question,
        history=history
    )

    # Kaynak tekrarlarını temizle
    unique_sources = []

    for source in sources:

        source_name = source.get(
            "source",
            "Bilinmeyen kaynak"
        )

        if source_name not in unique_sources:

            unique_sources.append(
                source_name
            )

    return {
        "answer": answer,
        "sources": unique_sources
    }