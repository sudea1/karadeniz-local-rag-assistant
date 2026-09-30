import os
import fitz
import chromadb
from sentence_transformers import SentenceTransformer


# PDF'lerin bulunduğu klasör
DATA_DIR = "../data"

# ChromaDB
client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="karadeniz_gezi"
)

# Türkçe için uygun çok dilli embedding modeli
model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)


def pdf_to_text(pdf_path):
    """
    PDF içerisindeki bütün metni çıkarır.
    """

    doc = fitz.open(pdf_path)

    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()

    return text


def chunk_text(text, chunk_size=800, overlap=150):
    """
    Uzun metni daha küçük parçalara böler.
    """

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def main():

    print("📚 PDF taraması başlıyor...")

    if not os.path.exists(DATA_DIR):

        print("❌ data klasörü bulunamadı!")

        return

    pdf_files = [
        file
        for file in os.listdir(DATA_DIR)
        if file.lower().endswith(".pdf")
    ]

    if not pdf_files:

        print("❌ data klasöründe PDF bulunamadı!")

        return

    print(f"✅ {len(pdf_files)} PDF bulundu.")

    total_chunks = 0

    for pdf_file in pdf_files:

        print()
        print("=" * 50)
        print(f"📄 İşleniyor: {pdf_file}")

        pdf_path = os.path.join(
            DATA_DIR,
            pdf_file
        )

        # PDF'den metin çıkar
        text = pdf_to_text(pdf_path)

        print(f"📝 Metin uzunluğu: {len(text)} karakter")

        if not text.strip():

            print("⚠️ Bu PDF'den metin çıkarılamadı.")

            continue

        # Metni parçalara ayır
        chunks = chunk_text(text)

        print(f"✂️ {len(chunks)} parça oluşturuldu.")

        # Embedding oluştur
        print("🧠 Embedding oluşturuluyor...")

        embeddings = model.encode(
            chunks,
            show_progress_bar=True
        ).tolist()

        city = os.path.splitext(pdf_file)[0]

        ids = [
            f"{city}_{i}"
            for i in range(len(chunks))
        ]

        metadatas = [
            {
                "city": city,
                "source": pdf_file
            }
            for _ in chunks
        ]

        # ChromaDB'ye ekle
        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )

        total_chunks += len(chunks)

        print(
            f"✅ {pdf_file} → "
            f"{len(chunks)} parça ChromaDB'ye eklendi."
        )

    print()
    print("=" * 50)
    print("🎉 PDF aktarımı tamamlandı!")
    print(f"📚 Toplam parça: {total_chunks}")
    print("=" * 50)


if __name__ == "__main__":
    main()