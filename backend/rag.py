import re
import time

import chromadb
from sentence_transformers import SentenceTransformer
import ollama


# ============================================================
# AYARLAR
# ============================================================

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "karadeniz_gezi"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_MODEL = "qwen2.5:3b-instruct"

SUPPORTED_CITIES = [
    "artvin",
    "giresun",
    "ordu",
    "rize",
    "samsun",
    "sinop",
    "trabzon",
]


# ============================================================
# CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_collection(
    name=COLLECTION_NAME
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL,
    local_files_only=True
)


# ============================================================
# ŞEHİR TESPİTİ
# ============================================================

def detect_city(question):
    question_lower = question.lower()

    for city in SUPPORTED_CITIES:
        if city in question_lower:
            return city

    return None


# ============================================================
# GEÇMİŞTEN ŞEHİR TESPİTİ
# ============================================================

def detect_city_from_history(question, history=None):

    # Önce mevcut soruya bak
    city = detect_city(question)

    if city:
        return city

    if not history:
        return None

    # En yeni mesajdan eskiye doğru ara
    for message in reversed(history):

        if message.get("role") != "user":
            continue

        content = message.get(
            "content",
            ""
        )

        city = detect_city(content)

        if city:
            return city

    return None


# ============================================================
# ROTA SORUSU TESPİTİ
# ============================================================

def is_route_question(question):
    question_lower = question.lower()

    route_keywords = [
        "rota",
        "rotası",
        "rotasi",
        "günlük gezi",
        "gunluk gezi",
        "günlük tur",
        "gunluk tur",
        "seyahat planı",
        "seyahat plani",
        "gezi planı",
        "gezi plani",
        "tur planı",
        "tur plani",
    ]

    return any(
        keyword in question_lower
        for keyword in route_keywords
    )


# ============================================================
# GEÇMİŞTE ROTA VAR MI?
# ============================================================

def was_route_context(history=None):

    if not history:
        return False

    for message in reversed(history[-6:]):

        if message.get("role") != "user":
            continue

        content = message.get(
            "content",
            ""
        )

        if is_route_question(content):
            return True

    return False


# ============================================================
# GÜN SAYISI TESPİTİ
# ============================================================

def detect_day_count(question):
    question_lower = question.lower()

    patterns = [
        r"(\d+)\s*günlük",
        r"(\d+)\s*gunluk",
        r"(\d+)\s*gün",
        r"(\d+)\s*gun",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            question_lower
        )

        if match:
            return int(match.group(1))

    return None


# ============================================================
# DEVAM SORUSU TESPİTİ
# ============================================================

def is_follow_up_question(question):

    question_lower = question.lower().strip()

    follow_up_phrases = [
        "başka",
        "başka?",
        "başka neler var",
        "başka neler var?",
        "başka nereler var",
        "başka nereler var?",
        "başka ne var",
        "başka ne var?",
        "bu kadar mı",
        "bu kadar mı?",
        "daha fazla",
        "devam",
        "peki",
        "peki başka",
        "tarihi olanlar",
        "doğal olanlar",
        "bunlardan",
        "bunu",
    ]

    if any(
        phrase in question_lower
        for phrase in follow_up_phrases
    ):
        return True

    # Çok kısa sorular çoğunlukla devam sorusudur.
    if len(question_lower.split()) <= 3:
        return True

    return False


# ============================================================
# SON ANA KULLANICI SORUSUNU BUL
# ============================================================

def find_previous_main_question(history=None):

    if not history:
        return None

    for message in reversed(history):

        if message.get("role") != "user":
            continue

        content = message.get(
            "content",
            ""
        ).strip()

        if not content:
            continue

        # "Başka?" gibi devam sorularını
        # ana bağlam olarak seçme.
        if is_follow_up_question(content):
            continue

        return content

    return None


# ============================================================
# ARAMA SORGUSU OLUŞTUR
# ============================================================

def build_search_query(question, history=None):

    question_clean = question.strip()

    if not history:
        return question_clean

    current_city = detect_city(question_clean)

    # Kullanıcı açıkça bir şehir söylediyse
    # yeni sorguyu eski şehir bağlamına bağlama.
    if current_city:
        return question_clean

    if not is_follow_up_question(question_clean):
        return question_clean

    previous_question = find_previous_main_question(
        history
    )

    if previous_question:

        return (
            f"{previous_question}. "
            f"Devam sorusu: {question_clean}"
        )

    recent_user_messages = []

    for message in history[-6:]:

        if message.get("role") == "user":

            content = message.get(
                "content",
                ""
            ).strip()

            if content:
                recent_user_messages.append(content)

    if recent_user_messages:

        return " ".join(
            recent_user_messages + [question_clean]
        )

    return question_clean


# ============================================================
# SOHBET GEÇMİŞİNİ METNE ÇEVİR
# ============================================================

def build_conversation_context(history=None):

    if not history:
        return "Önceki konuşma bulunmuyor."

    conversation_lines = []

    # Prompt gereksiz büyümesin.
    for message in history[-8:]:

        role = message.get("role")

        content = message.get(
            "content",
            ""
        ).strip()

        if not content:
            continue

        if role == "user":

            conversation_lines.append(
                f"Kullanıcı: {content}"
            )

        elif role == "assistant":

            conversation_lines.append(
                f"Asistan: {content}"
            )

    if not conversation_lines:
        return "Önceki konuşma bulunmuyor."

    return "\n".join(
        conversation_lines
    )


# ============================================================
# RAG SEARCH
# ============================================================

def search_documents(
    question,
    history=None,
    n_results=6
):

    # --------------------------------------------------------
    # BAĞLAM
    # --------------------------------------------------------

    city = detect_city_from_history(
        question,
        history
    )

    route_mode = is_route_question(
        question
    )

    search_query = build_search_query(
        question,
        history
    )

    # --------------------------------------------------------
    # EMBEDDING + SÜRE ÖLÇÜMÜ
    # --------------------------------------------------------

    embedding_start = time.perf_counter()

    question_embedding = embedding_model.encode(
        search_query
    ).tolist()

    embedding_time = (
        time.perf_counter()
        - embedding_start
    )

    # --------------------------------------------------------
    # CHROMADB + SÜRE ÖLÇÜMÜ
    # --------------------------------------------------------

    chroma_start = time.perf_counter()

    # Genel Karadeniz rotası
    if route_mode and not city:

        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=15,
        )

    # Belirli şehir
    elif city:

        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=8 if route_mode else 6,
            where={
                "city": city
            },
        )

    # Genel normal soru
    else:

        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=n_results,
        )

    chroma_time = (
        time.perf_counter()
        - chroma_start
    )

    # --------------------------------------------------------
    # SONUÇLAR
    # --------------------------------------------------------

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    print("\n🔍 ChromaDB arama bilgisi:")

    if route_mode:
        print("Mod: 🗺️ ROTA")
    else:
        print("Mod: 💬 NORMAL")

    if city:
        print(f"Aktif şehir: {city}")
    else:
        print("Aktif şehir: Yok")

    print(
        f"Arama sorgusu: {search_query}"
    )

    print("\n⚡ Performans:")

    print(
        f"Embedding: {embedding_time:.2f} sn"
    )

    print(
        f"ChromaDB: {chroma_time:.2f} sn"
    )

    print("\nSeçilen kaynaklar:")

    for metadata in metadatas:

        print(
            f"- {metadata.get('source', 'Bilinmeyen kaynak')}"
        )

    return documents, metadatas


# ============================================================
# QWEN + RAG
# ============================================================

def ask_rag(
    question,
    history=None
):

    total_start = time.perf_counter()

    # --------------------------------------------------------
    # ARAMA
    # --------------------------------------------------------

    documents, metadatas = search_documents(
        question,
        history=history,
        n_results=6
    )

    if not documents:

        return (
            "Bu soruyla ilgili kaynaklarda yeterli bilgi bulamadım.",
            []
        )

    # --------------------------------------------------------
    # RAG CONTEXT
    # --------------------------------------------------------

    context_parts = []

    for document, metadata in zip(
        documents,
        metadatas
    ):

        source = metadata.get(
            "source",
            "Bilinmeyen kaynak"
        )

        context_parts.append(
            f"""
Kaynak: {source}

İçerik:
{document}
"""
        )

    context = "\n\n".join(
        context_parts
    )

    # --------------------------------------------------------
    # SOHBET CONTEXT
    # --------------------------------------------------------

    conversation_context = build_conversation_context(
        history
    )

    active_city = detect_city_from_history(
        question,
        history
    )

    search_context = build_search_query(
        question,
        history
    )

    # --------------------------------------------------------
    # ROTA MODU
    # --------------------------------------------------------

    route_mode = is_route_question(
        question
    )

    # "Bunu 2 güne indir" gibi bir mesajsa
    # geçmişte rota olup olmadığına da bak.
    if (
        not route_mode
        and history
        and detect_day_count(question)
        and was_route_context(history)
    ):
        route_mode = True

    day_count = detect_day_count(
        question
    )

    # ========================================================
    # ROTA PROMPT
    # ========================================================

    if route_mode:

        if day_count:

            day_instruction = f"""
Kullanıcı TAM OLARAK {day_count} günlük bir rota istemektedir.

ÇOK ÖNEMLİ:
- Rota TAM OLARAK {day_count} gün olmalıdır.
- {day_count} günden fazla gün oluşturma.
- {day_count} günden az gün oluşturma.
- Son gün "{day_count}. Gün" olmalıdır.
"""

        else:

            day_instruction = """
Kullanıcı belirli bir gün sayısı belirtmemiştir.
Kaynaklara uygun ve makul uzunlukta bir rota oluştur.
"""

        prompt = f"""
Sen yerel çalışan, samimi ve yardımcı bir
Karadeniz Gezi Asistanısın.

Kullanıcıyla doğal bir sohbet yapıyormuş gibi konuş.

{day_instruction}

Aktif şehir:
{active_city if active_city else "Belirli bir şehir yok"}

ÖNCEKİ KONUŞMA:

{conversation_context}

ARAMA İÇİN KORUNAN BAĞLAM:

{search_context}

Yalnızca aşağıda verilen kaynak bilgilerini kullan.

Kaynaklarda bulunmayan yerleri, özellikleri veya bilgileri
kesinlikle uydurma.

KURALLAR:

- Cevabını mutlaka Türkçe ver.

- Samimi, doğal ve yardımcı bir dil kullan.

- Önceki konuşmayı dikkate al.

- Kullanıcının önceki mesajlarında belirttiği şehir,
  kapsam ve tercihleri koru.

- Gün sayısı belirtildiyse bu sayıya kesinlikle uy.

- Her günü ayrı başlık altında göster.

- Her gün için kaynaklarda yeterli bilgi varsa
  2-3 gezi noktası öner.

- Aynı şehirde bulunan yerleri mümkün olduğunca
  aynı güne yerleştir.

- Her güne farklı şehir koymak zorunda değilsin.

- Aynı gezi noktasını farklı günlerde tekrar etme.

- Rotayı mümkün olduğunda
  Sabah / Öğleden Sonra / Akşam şeklinde düzenle.

- Kaynaklarda akşam için uygun bilgi yoksa
  yeni bilgi uydurma.

- Her gezi noktası için kısa ve faydalı
  bir açıklama yap.

- Kaynaklarda olmayan mesafe, ulaşım süresi,
  fiyat veya çalışma saatlerini uydurma.

- Gereksiz yere çok fazla şehir ekleme.

- Kullanıcı yeni bir şehir söylerse
  eski şehir bağlamını bırak.

- Düşünme veya analiz sürecini kullanıcıya gösterme.

CEVAP FORMATI:

🗺️ {day_count if day_count else ""} Günlük Karadeniz Rotası

📍 1. Gün — Şehir

🌅 Sabah:
Yer adı — kısa açıklama

☀️ Öğleden Sonra:
Yer adı — kısa açıklama

🌙 Akşam:
Kaynaklarda uygun bir öneri varsa yaz.

Diğer günleri aynı formatta devam ettir.

{
    f"Rota kesinlikle {day_count}. Gün ile bitmelidir. "
    f"{day_count + 1}. Gün oluşturma."
    if day_count
    else ""
}

💡 Rota Notu:
Rotayla ilgili kaynaklara dayalı kısa bir değerlendirme yap.

Kullanıcının mevcut sorusu:
{question}

KAYNAK BİLGİLER:

{context}

Şimdi kullanıcıya doğal ve kaynaklara sadık
bir Türkçe rota oluştur:
"""

    # ========================================================
    # NORMAL SOHBET PROMPT
    # ========================================================

    else:

        prompt = f"""
Sen yerel çalışan, samimi ve yardımcı bir
Karadeniz Gezi Asistanısın.

Bir arama motoru gibi sadece yer isimleri sıralamak yerine,
kullanıcıyla doğal bir sohbet yapıyormuş gibi cevap ver.

Aktif şehir:
{active_city if active_city else "Belirli bir şehir yok"}

ÖNCEKİ KONUŞMA:

{conversation_context}

ARAMA İÇİN KORUNAN BAĞLAM:

{search_context}

Kullanıcının mevcut sorusuna yalnızca aşağıdaki
kaynak bilgileri kullanarak cevap ver.

KURALLAR:

1. Cevabını mutlaka Türkçe ver.

2. Samimi, doğal ve yardımcı bir üslup kullan.
   Kullanıcıyla gezi hakkında sohbet ediyormuş gibi konuş.

3. Sadece yer isimlerini virgülle veya alt alta sıralama.

4. Cevaba kısa ve doğal bir giriş cümlesiyle başla.

   Örneğin:
   "Rize şehir merkezindeysen birkaç güzel seçeneğin var 🌿"

   veya:

   "Tabii, birkaç alternatif daha var 😊"

   Bu örnekleri birebir kullanmak zorunda değilsin.
   Sorunun bağlamına uygun doğal bir giriş oluştur.

5. Önerdiğin her yer için kaynaklarda bulunan bilgilere
   dayanarak 1-2 kısa cümle açıklama yap.

6. Uygun olduğunda emoji kullanabilirsin fakat abartma.

7. Önceki konuşmayı mutlaka dikkate al.

8. Kullanıcının önceki mesajlarında belirttiği kapsamları koru.

   Örneğin kullanıcı:

   "Rize şehir merkezinde ne yapabilirim?"

   dediyse daha sonraki:

   "başka?"
   "başka neler var?"
   "bu kadar mı?"

   sorularında ŞEHİR MERKEZİ kapsamı devam eder.

9. Kullanıcı şehir merkezi istemişse,
   şehir merkezi dışında olduğu kaynaklardan anlaşılan
   yayla, köy, ilçe veya uzak gezi noktalarını sırf daha
   fazla öneri vermek için ekleme.

10. Kullanıcı "başka" veya "daha fazla" diyorsa,
    önceki cevapta önerilen yerleri mümkün olduğunca tekrar etme.

11. Kullanıcı:

    "tarihi olanlar"
    "doğal yerler"
    "müzeler"
    "yaylalar"

    gibi yeni bir tercih belirtirse aktif şehir bağlamını
    koruyarak bu tercihe göre cevap ver.

12. Kullanıcı yeni bir şehir söylerse eski şehir bağlamını
    bırak ve yeni şehre geç.

13. Kaynaklarda kullanıcının istediği kapsamda yeterli yer
    yoksa kapsam dışındaki yerleri sırf cevap vermek için ekleme.

    Bunun yerine doğal bir şekilde söyle.

    Örneğin:

    "Kaynaklarımda şehir merkezi için başka net bir öneri
    görünmüyor. İstersen Rize genelindeki yerlere de
    geçebiliriz."

14. Kaynaklarda olmayan bilgileri kesinlikle uydurma.

15. İnternetten veya kendi genel bilginden bilgi ekleme.

16. Kaynaklarda olmayan mesafe, ulaşım süresi,
    fiyat veya çalışma saatlerini tahmin etme.

17. Normal gezi önerilerinde kaynaklarda yeterli bilgi
    varsa 3-5 seçenek sun.

    Ancak sayı tamamlamak için kapsam dışına çıkma.

18. Önceki cevapta bir yer önerilmişse ve kullanıcı
    "başka" diyorsa mümkün olduğunca farklı yerler öner.

19. Kullanıcının sorusuna gereksiz derecede uzun cevap verme.
    Sohbet havasında, okunabilir ve faydalı cevap ver.

20. Düşünme veya analiz sürecini kullanıcıya gösterme.

21. Kullanıcı belirli bir yer TÜRÜ istiyorsa (örn. "yayla",
    "kale", "şelale", "müze", "plaj"), SADECE o türdeki yerleri
    öner. Kaynaklarda başka türde (örn. kale, müze, anıt) yerler
    de geçse bile, kullanıcının istediği türe uymuyorsa cevaba
    ekleme.

Kullanıcının mevcut sorusu:
{question}

KAYNAK BİLGİLER:

{context}

Şimdi kullanıcıya doğal, samimi ve kaynaklara sadık
bir Türkçe cevap ver:
"""

    # ========================================================
    # OLLAMA (STREAMING)
    # ========================================================

    try:

        ollama_start = time.perf_counter()

        # num_predict: rota modunda daha uzun cevaba izin ver,
        # normal sohbette daha kısa tut.
        # Model düşünme metni üretirse bile marker sonrası gerçek
        # cevaba yetecek pay bırakmak için tavanı biraz yüksek tuttuk.
        max_tokens = 1600 if route_mode else 900

        ANSWER_MARKER = "===CEVAP==="

        stream = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sen Türkçe cevap veren samimi bir "
                        "Karadeniz Gezi Asistanısın. "
                        "Yalnızca verilen kaynakları kullan. "
                        "Kullanıcıyla doğal bir sohbet yap. "
                        f"ÇOK ÖNEMLİ FORMAT KURALI: Yanıtına, başka "
                        f"hiçbir şey yazmadan, tam olarak şu satırla "
                        f"başla: {ANSWER_MARKER} — Bu satırdan önce "
                        f"planlama, analiz, açıklama veya düşünce "
                        f"YAZMA. {ANSWER_MARKER} satırından hemen "
                        f"sonra doğrudan nihai Türkçe cevabı yaz."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        prompt
                        + f"\n\nUnutma: yanıtına başka hiçbir şey "
                        f"yazmadan '{ANSWER_MARKER}' satırıyla başla, "
                        f"sonra doğrudan Türkçe cevabı yaz."
                    )
                }
            ],
            think=False,  # destekleniyorsa thinking'i kapatır (ek önlem)
            options={
                "temperature": 0.3,
                "num_ctx": 4096,
                "num_predict": max_tokens,
            },
            keep_alive="30m",
            stream=True
        )

        # --------------------------------------------------------
        # STREAM'İ TÜKET
        # --------------------------------------------------------
        # NOT: Model bazen talimat cümlesi içindeki marker'ı da
        # (tırnak içinde geçtiği için) aynen tekrar edebiliyor.
        # Bu yüzden İLK görülen değil, EN SON görülen marker esas
        # alınır; canlı yazdırma da stream bitene kadar ertelenir.

        raw_answer = ""
        final_chunk = None

        for chunk in stream:
            piece = chunk["message"]["content"]
            raw_answer += piece
            final_chunk = chunk

        ollama_time = (
            time.perf_counter()
            - ollama_start
        )

        # --------------------------------------------------------
        # NİHAİ CEVABI ÇIKAR (en son marker'dan sonrası)
        # --------------------------------------------------------

        marker_idx = raw_answer.rfind(ANSWER_MARKER)

        if marker_idx != -1:
            answer = raw_answer[marker_idx + len(ANSWER_MARKER):]
        else:
            # Marker hiç gelmediyse, olası <think> bloklarını
            # en azından temizlemeyi dene.
            answer = re.sub(
                r"<think>.*?</think>",
                "",
                raw_answer,
                flags=re.DOTALL
            )

        answer = answer.strip()

        # Cevabı tek seferde yazdır (stream boyunca yanlışlıkla
        # yarım/hatalı içerik basılmasın diye)
        print(answer, end="", flush=True)

        # --------------------------------------------------------
        # OLLAMA PERFORMANS DETAYLARI (son chunk'tan)
        # --------------------------------------------------------

        if final_chunk:

            load_duration = (
                final_chunk.get("load_duration", 0)
                / 1_000_000_000
            )

            prompt_eval_duration = (
                final_chunk.get("prompt_eval_duration", 0)
                / 1_000_000_000
            )

            eval_duration = (
                final_chunk.get("eval_duration", 0)
                / 1_000_000_000
            )

            prompt_eval_count = final_chunk.get(
                "prompt_eval_count",
                0
            )

            eval_count = final_chunk.get(
                "eval_count",
                0
            )

            print(
                f"\n\n⚡ Qwen toplam: "
                f"{ollama_time:.2f} sn"
            )

            print("\n📊 Ollama detayları:")

            print(
                f"Model yükleme: "
                f"{load_duration:.2f} sn"
            )

            print(
                f"Prompt işleme: "
                f"{prompt_eval_duration:.2f} sn"
            )

            print(
                f"Prompt token: "
                f"{prompt_eval_count}"
            )

            print(
                f"Cevap üretme: "
                f"{eval_duration:.2f} sn"
            )

            print(
                f"Üretilen token: "
                f"{eval_count}"
            )

            if eval_duration > 0:

                tokens_per_second = (
                    eval_count
                    / eval_duration
                )

                print(
                    f"Üretim hızı: "
                    f"{tokens_per_second:.2f} token/sn"
                )

        total_time = (
            time.perf_counter()
            - total_start
        )

        print(
            f"\n⚡ Toplam RAG süresi: "
            f"{total_time:.2f} sn"
        )

        print(
            "\n🧠 Ollama cevap kontrolü:"
        )

        print(
            f"Content uzunluğu: "
            f"{len(answer) if answer else 0}"
        )

        if not answer:

            print(
                "⚠️ Qwen boş content döndürdü."
            )

            return (
                "Kaynakları buldum ancak model şu anda "
                "cevap oluşturamadı. Soruyu tekrar deneyebilirsin.",
                metadatas
            )

        return answer, metadatas

    except Exception as error:

        print(
            f"\n❌ Ollama hatası: {error}"
        )

        return (
            "Yerel yapay zekâ modeline bağlanırken "
            "bir hata oluştu.",
            metadatas
        )


# ============================================================
# TERMINAL TESTİ
# ============================================================

if __name__ == "__main__":

    print(
        "\n🌊 Karadeniz Gezi Asistanı"
    )

    print(
        "Çıkmak için 'exit' yazabilirsin.\n"
    )

    terminal_history = []

    while True:

        question = input(
            "Sorunuz: "
        ).strip()

        if question.lower() in [
            "exit",
            "quit",
            "çıkış"
        ]:

            print(
                "\nGörüşürüz! 👋"
            )

            break

        if not question:
            continue

        print(
            "\n🤖 Cevap hazırlanıyor...\n"
        )

        # NOT: answer, ask_rag içinde stream olarak zaten
        # ekrana basılıyor; burada tekrar print(answer) yapmıyoruz.
        answer, sources = ask_rag(
            question,
            history=terminal_history
        )

        print("\n" + "=" * 60)

        # --------------------------------------------------------
        # SOHBET HAFIZASINA EKLE
        # --------------------------------------------------------

        terminal_history.append(
            {
                "role": "user",
                "content": question
            }
        )

        terminal_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        terminal_history = terminal_history[-12:]

        # --------------------------------------------------------
        # KAYNAKLAR
        # --------------------------------------------------------

        if sources:

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

            print(
                "\n📚 Kullanılan kaynaklar:"
            )

            for source_name in unique_sources:

                print(
                    f"- {source_name}"
                )

        print()