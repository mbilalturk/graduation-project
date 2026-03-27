# Traffic Data Sources Research for Route 502 Bus Corridor

**Tarih:** 2026-03-27

Bu rapor, Izmir Route 502 otobus koridoru icin trafik yogunlugu verisi elde etme seceneklerini arastirmaktadir.

---

## 1. Izmir Belediyesi Acik Veri Portali (acikveri.bizizmir.com)

### 1a. Ana Arterler Gunluk Hiz ve Sure Verileri

- **URL:** https://acikveri.bizizmir.com/tr/dataset/ana-arterler-gunluk-hiz-ve-sure-verileri
- **Icerik:** 4 ana arterde (Yesildere Cad., Mustafa Kemal Sahil Bulvari, Anadolu Cad., Ankara Cad.) gunluk hiz ve seyahat suresi olcumleri
- **Veri Alanlari:** Seyahat suresi (dakika), hesaplanmis hiz (km/mesafe bolme sure)
- **Toplama Yontemi:** IZUM trafik denetim ekibi is gunlerinde manuel olcum
- **Format:** XLSX, CSV, JSON, XML (API ile de erisim var)
- **Guncelleme:** Haftalik (son guncelleme: 19 Mart 2026)
- **Ucret:** Ucretsiz

**Degerlendirme:** Route 502 bu 4 arterin disinda kaliyor (Bornova-Buca hatti). Dolayisiyla dogrudan Route 502 koridor verisini kapsamiyor, ancak genel sehir trafik trendi icin kullanilabilir. Mevcut proje icin **sinirli faydali**.

### 1b. Arac Sayim Verileri

- **URL:** acikveri.bizizmir.com uzerinde mevcut
- **Icerik:** 3 ana guzergahta kameralardan arac sayimi, rush hour donemleri (07:00-09:30, 18:00-19:30)
- **Degerlendirme:** Hacim verisi, hiz/yogunluk degil. Route 502 ile kesisim bilinmiyor.

### 1c. Arizali/Kazali Arac Verileri

- Kaza konum ve mudahale suresi bilgileri
- Ek bir trafik bozucu faktor olarak kullanilabilir, ancak yuksek oncelikli degil.

---

## 2. Izmir Teknoloji (iztek) API — Mevcut Proje API'si

- **Endpointler:** `hatotobuskonumlari`, `duragayaklasanotobusler`, `hattinyaklasanotobusleri`
- **Trafik Verisi:** YOK. API yalnizca otobus GPS konumlari ve durak yaklasma bilgisi sunuyor.
- **Dolayil Kullanim:** Otobus hiz verisi (konum farki / zaman farki) trafik yogunlugu icin proxy olarak kullanilabilir (asagida Secenk 7'ye bakiniz).

---

## 3. Google Maps Routes API (TRAFFIC_AWARE)

- **Endpoint:** `computeRoutes` ile `TRAFFIC_AWARE` veya `TRAFFIC_AWARE_OPTIMAL` routing modifiers
- **Veri:** Trafik-farkinda seyahat suresi tahmini, alternatif rotalar
- **Ucretsiz Tier:** 5,000 istek/ay (Pro SKU, Mart 2025 fiyatlandirmasi)
- **Ucretli:** ~$10 / 1,000 istek
- **Sorgulama:** Origin + Destination koordinatlari ile rota bazli sorgulama
- **Donus Verisi:** `duration` (trafik dahil), `staticDuration` (trafiksiz), `distanceMeters`
- **Avantajlar:** En genis kapsam, guvenilir veri, Izmir'de calisiyor
- **Dezavantajlar:** Sadece seyahat suresi veriyor (hiz/yogunluk seviyesi yok), 5K/ay siniri Route 502'nin 32 segmenti icin yetersiz olabilir (32 segment x 24 saat x 30 gun = ~23,040 istek/ay)
- **Maliyet Tahmini:** 5K ucretsiz + 18K ucretli = ~$180/ay

**Degerlendirme:** Zengin ve guvenilir ama akademik proje icin pahali. Dusuk frekansta ornekleme (her 15 dk yerine saatte 1) ile 5K limitte kalinable: 32 segment x 18 saat x 30 gun / 1 = ~17,280 (hala asim).

---

## 4. TomTom Traffic Flow API

- **Endpoint:** Flow Segment Data — koordinata en yakin yol segmentinin trafik bilgisi
- **Veri Alanlari:**
  - `currentSpeed` — Anlik hiz (km/h)
  - `freeFlowSpeed` — Serbest akis hizi
  - `currentTravelTime` — Mevcut seyahat suresi (sn)
  - `freeFlowTravelTime` — Serbest akis seyahat suresi (sn)
  - `confidence` — Guvenilirlik skoru (0-100)
  - `roadClosure` — Yol kapanikligi durumu
- **Ucretsiz Tier:** 2,500 non-tile istek/GUN (aylik ~75,000)
- **Ucretli:** $0.75 / 1,000 istek
- **Guncelleme:** Her dakika guncellenen veri
- **Sorgulama:** Enlem/boylam koordinati ile en yakin yol segmenti

**Degerlendirme: EN IYI SECENEK.** 2,500/gun limiti cok comert. Route 502 icin ornek hesap:
- 32 durak arasi segment x her 5 dk'da 1 sorgu x 18 saat = 6,912 istek/gun (sinirin 2.7 kati)
- 32 segment x her 15 dk'da 1 sorgu x 18 saat = 2,304 istek/gun (SINIR ICINDE)
- Dakikada guvenilir, anlik hiz + serbest akis hizi + confidence skoru

**Oneri:** 15 dakikalik ornekleme ile ucretsiz tier icinde kalinabilir. Trafik yogunluk orani = `currentSpeed / freeFlowSpeed` olarak hesaplanabilir.

---

## 5. HERE Traffic API v7

- **Endpoint:** Flow endpoint — bounding box veya koridor bazli trafik akisi
- **Veri Alanlari:**
  - `speed` — Beklenen hiz (m/s)
  - `speedUncapped` — Hiz limiti asilabilir
  - `freeFlow` — Serbest akis hizi (m/s)
  - `jamFactor` — Yogunluk skoru (0.0 = serbest, 10.0 = tikanik)
  - `jamTendency` — Yogunluk egilimi (artis/azalis)
  - `traversability` — Gecis durumu
- **Ucretsiz Tier:** 5,000 istek/ay (sinirli)
- **Ucretli:** $2.50 / 1,000 istek
- **Fiyat Notu:** Nisan 2026'da %6 fiyat artisi duyuruldu

**Degerlendirme:** `jamFactor` cok kullanisli bir feature (dogrudan ML'ye girer). Ancak 5K/ay siniri cok dusuk — Route 502'nin 32 segmenti icin gunluk ~170 sorgu yapilabilir (saatte ~9 sorgu). Dusuk cozunurluk icin kullanilabilir ama TomTom'a gore dezavantajli.

---

## 6. Yandex Maps Router API

- **Turkiye Kapsami:** Var, Izmir dahil. Yandex Turkiye'de guclu varligi var.
- **Veri:** Trafik tahminli rota suresi, trafik siklari
- **Ucretsiz Tier:** 25,000 MAU (MapKit SDK icin); Router API icin sinirli ucretsiz erisim, detaylar belirsiz
- **Ucretli:** Basic plan 2.5M istek/yil icin $1,625 (~$135/ay)
- **Sorgulama:** Origin-Destination bazli routing
- **Startup Programi:** Turk startup'lara ucretsiz API erisimi (basvuru ile)

**Degerlendirme:** Fiyatlandirma belirsiz ve Router API segment bazli trafik verisi degil, rota bazli seyahat suresi veriyor. TomTom'a gore dezavantajli. Startup programi akademik proje icin uygun olmayabilir.

---

## 7. ONEMLI: Otobus GPS Hizindan Trafik Cikarimi (Sifir Maliyet)

Akademik literaturde guclenerek desteklenen bir yaklasim: **Otobus AVL/GPS verisinden trafik yogunlugu cikarimi.**

### Yontem
Mevcut `collector.py` ile toplanan GPS verisi zaten segment bazli seyahat surelerini icerir. Bu veriden:

1. **Anlik otobus hizi** = segment mesafesi / seyahat suresi
2. **Normalize hiz** = anlik hiz / tarihsel ortalama hiz (ayni segment, ayni saat)
3. **Yogunluk seviyesi** = normalize hiz < 0.5 ise "yogun", 0.5-0.8 "orta", > 0.8 "serbest"

### Destekleyen Literatur
- "Using High-Resolution Bus GPS Data to Visualize and Identify Congestion Hot Spots" (ResearchGate)
- "Predicting On-road Traffic Congestion from Public Transport GPS Data" (Academia.edu)
- "Visualization and Assessment of the Effect of Roadworks on Traffic Congestion Using AVL Data" (Springer)
- "Ensemble ML Approach for Traffic Congestion and Travel Time Prediction in Urban BRT Systems" (MDPI)

### Avantajlar
- **Sifir ek maliyet** — zaten toplanan veriyi kullanir
- **Akademik olarak guclu** — birden fazla yayinla destekleniyor
- **Route 502'ye ozgu** — tam olarak hedef koridor uzerinde olcum
- **Feature olarak ML'ye girer** — `speed_ratio`, `historical_speed_deviation` gibi turemiş feature'lar

### Sinirlamalar
- Sadece otobus guzergahindaki yollari kapsar
- Dwell time (durakta bekleme) ile trafik yavaslamasi ayristirmasi gerekir
- Otobus sayisi az ise (gece) cozunurluk dusuk

---

## Ozet ve Oneri Tablosu

| Kaynak | Veri Turu | Ucretsiz Limit | Maliyet | Route 502 Uygunlugu | Oncelik |
|--------|-----------|----------------|---------|---------------------|---------|
| **Otobus GPS Cikarimi** | Hiz, yogunluk orani | Sinirsiz | $0 | MUKEMMEL | **1 (BIRINCIL)** |
| **TomTom Traffic Flow** | Hiz, serbest akis hizi, confidence | 2,500/gun | $0.75/1K | COKIYI (15dk ornekleme) | **2 (TAKVIYE)** |
| **Izmir Acik Veri (Ana Arterler)** | Hiz, sure | Sinirsiz | $0 | DUSUK (farkli arterler) | 3 (REFERANS) |
| **Google Routes API** | Seyahat suresi | 5,000/ay | $10/1K | ORTA (pahali) | 4 |
| **HERE Traffic v7** | Hiz, jamFactor | 5,000/ay | $2.50/1K | DUSUK (az istek) | 5 |
| **Yandex Router** | Seyahat suresi | Belirsiz | ~$135/ay | DUSUK (belirsiz) | 6 |

---

## Onerilen Strateji

### Katman 1 — Birincil (Sifir Maliyet)
Mevcut otobus GPS verisinden trafik feature'lari turetmek:
- `segment_speed_kmh` = mesafe / seyahat suresi
- `speed_ratio` = anlik hiz / tarihsel ortalama hiz (ayni saat, ayni gun tipi)
- `is_congested` = speed_ratio < 0.6
- `congestion_level` = kategorik (serbest / orta / yogun / tikanik)

Bu feature'lar `feature_engineering.ipynb` icerisine eklenebilir, ek API gerekmiyor.

### Katman 2 — Takviye (Ucretsiz TomTom)
TomTom Traffic Flow API ile 15 dakikalik aralarda Route 502 segmentlerinin trafik durumunu toplamak:
- Collector'a yeni bir fonksiyon eklemek: `collect_traffic_data()`
- Her 15 dk'da 32 segment = gunluk ~2,304 istek (2,500 siniri icinde)
- Ek feature: `tomtom_speed`, `tomtom_freeflow_speed`, `tomtom_confidence`, `tomtom_congestion_ratio`

### Katman 3 — Dogrulama (Opsiyonel)
Google Routes API ile gunluk 1-2 kez rota bazli seyahat suresi kontrolu (ground truth karsilastirmasi icin).

---

## Sonraki Adimlar

1. Feature engineering notebook'una GPS-bazli trafik feature'larini ekle (Katman 1)
2. TomTom Developer hesabi ac ve API key al (ucretsiz, kredi karti gerektirmez)
3. Collector'a TomTom Traffic polling fonksiyonu ekle (Katman 2)
4. Yeni feature'larla ablation study tekrarla — trafik bilgisinin model performansina etkisini olc
