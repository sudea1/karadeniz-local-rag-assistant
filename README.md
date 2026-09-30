# 🌊 Karadeniz Local RAG Travel Assistant

Karadeniz Bölgesi için geliştirilmiş, tamamen yerel olarak çalışabilen
RAG (Retrieval-Augmented Generation) tabanlı yapay zekâ gezi asistanı.

Proje, kullanıcıların doğal dilde sordukları sorulara Karadeniz şehirleri
hakkında hazırlanan dokümanlardan bilgi getirerek yanıt üretir.

## ✨ Özellikler

- 🗺️ Karadeniz şehirleri hakkında gezi önerileri
- 🏔️ Yayla, tarihi yer ve doğal güzellik önerileri
- 🍽️ Yöresel yemek önerileri
- 🗓️ Çok günlük gezi rotaları oluşturma
- 💬 Devam sorularında konuşma bağlamını koruma
- 📚 Doküman tabanlı RAG sistemi
- 🔎 Semantic search
- 💻 Tamamen yerel LLM kullanımı
- 🌐 Gerekli modeller indirildikten sonra internet olmadan çalışabilme

## 🧠 Sistem Mimarisi

PDF Dokümanları  
↓  
Text Chunking  
↓  
Sentence Transformers Embedding  
↓  
ChromaDB  
↓  
Semantic Search  
↓  
Qwen3 4B + Ollama  
↓  
FastAPI  
↓  
Next.js / React Arayüzü

## 🛠️ Kullanılan Teknolojiler

### AI & Backend
- Python
- FastAPI
- Ollama
- Qwen3 4B
- Sentence Transformers
- ChromaDB

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS

## 📚 RAG Yapısı

Karadeniz şehirleriyle ilgili dokümanlar parçalara ayrılarak
embedding vektörlerine dönüştürülür ve ChromaDB içerisinde saklanır.

Kullanıcı bir soru sorduğunda sistem semantic search kullanarak
soruyla en alakalı içerikleri bulur.

Bulunan içerikler Qwen3 modeline bağlam olarak gönderilir ve model
bu kaynaklara dayanarak kullanıcıya doğal dilde cevap oluşturur.

## 🗺️ Desteklenen Şehirler

- Artvin
- Giresun
- Ordu
- Rize
- Samsun
- Sinop
- Trabzon

## 🚀 Çalıştırma

### Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1
uvicorn api:app --reload
