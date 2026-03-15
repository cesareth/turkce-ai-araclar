import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class Request(BaseModel):
    tool: str
    input: str
    extra: dict = {}

PROMPTS = {
    "kvkk": """Sen bir KVKK (6698 Sayılı Kişisel Verilerin Korunması Kanunu) uzmanısın.
Aşağıdaki metni KVKK uyumu açısından analiz et.

Şu formatta yanıt ver:
## Uyum Puanı: X/100

## ✅ Uyumlu Maddeler
- (liste)

## ❌ Eksik / Sorunlu Maddeler
- (madde no ve açıklama)

## 📋 Öneriler
- (somut düzeltme önerileri)

## 📄 Düzeltilmiş Metin
(eğer kısa bir metinse, düzeltilmiş halini yaz)

Metin:
{input}""",

    "dilekce": """Sen bir Türk hukuk ve bürokrasi uzmanısın. Aşağıdaki bilgilere göre resmi bir {tip} yaz.
Türk bürokrasisinin resmi yazışma formatına tam uygun, imzaya hazır belge oluştur.

Bilgiler:
{input}

Belge formatı:
- Başlık (kuruma hitap)
- Konu satırı
- Giriş paragrafı
- Ana içerik (madde madde)
- Sonuç ve talep
- Tarih ve imza bölümü""",

    "duzeltici": """Sen bir Türk dili uzmanısın. Aşağıdaki metni düzelt:

1. TDK yazım kurallarına uygunluk
2. Yabancı kelimelerin Türkçe karşılığı (varsa)
3. Üslup ve akıcılık
4. Noktalama işaretleri

Şu formatta yanıt ver:
## ✏️ Düzeltilmiş Metin
(düzeltilmiş metin)

## 📝 Yapılan Değişiklikler
- (değişiklik listesi, kısa)

Metin:
{input}""",

    "kod": """Sen bir kıdemli Türk yazılım geliştiricisisin. Aşağıdaki koda Türkçe yorum satırları ve docstring ekle.

Kurallar:
- Yorumlar Türkçe, nokta ile biter
- Ne yaptığını değil, neden yaptığını açıkla
- Fonksiyonlara docstring ekle (parametreler, dönüş değeri)
- Mevcut İngilizce yorumları Türkçeye çevir

Kod:
{input}"""
}

@app.post("/api/process")
async def process(req: Request):
    if req.tool not in PROMPTS:
        return {"error": "Geçersiz araç"}

    prompt_template = PROMPTS[req.tool]

    if req.tool == "dilekce":
        tip = req.extra.get("tip", "dilekçe")
        prompt = prompt_template.format(input=req.input, tip=tip)
    else:
        prompt = prompt_template.format(input=req.input)

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return {"result": message.content[0].text}

@app.get("/", response_class=HTMLResponse)
async def index():
    return open("index.html").read()
