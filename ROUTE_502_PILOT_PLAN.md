# Route 502 (Cengizhan - Halkapinar Metro) Pilot Plan

## 1. Rota Kimlik Bilgileri

| Alan | Deger |
|------|-------|
| Route ID | 502 |
| Hat Adi | CENGİZHAN - HALKAPINAR METRO |
| Guzergah | Bayrakli Sehir Hastanesi - Manas Bulv - Adliye - Cinarli EML |
| Baslangic | Cengizhan |
| Bitis | Halkapinar Metro |
| Route Type | 3 (Bus) |

---

## 2. Veri Envanter Ozeti

### GTFS Verileri

| Kaynak | Route 502 Kayit Sayisi | Detay |
|--------|----------------------|-------|
| stop_times.txt | 18,244 | Ana tahmin verisi |
| trips.txt | 608 | 305 gidis + 303 donus |
| stops (unique) | 58 | Rota uzerindeki duraklar |
| shapes.txt | 715 | 382 (gidis) + 333 (donus) nokta |

### CSV Verileri

| Kaynak | Route 502 Kayit Sayisi | Detay |
|--------|----------------------|-------|
| hat-guzergahlari.csv | 1,596 | 824 (yon 1) + 772 (yon 2) GPS nokta |
| hareketsaatleri.csv | 642 | 510 hafta ici + 76 cumartesi + 56 pazar |
| hatlari.csv | 1 | Hat meta bilgisi |

### Toplam Kullanilabilir Veri: ~21,300 kayit

---

## 3. Sefer Bilgileri

### Servis Takvimi (GTFS calendar)

| Service ID | Pazartesi | Sali | Carsamba | Persembe | Cuma | Cumartesi | Pazar | Donem |
|------------|-----------|------|----------|----------|------|-----------|-------|-------|
| 2917 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 23 Tem - 23 Eyl 2024 |
| 2926 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 27 Tem - 27 Eyl 2024 |
| 2929 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 28 Tem - 28 Eyl 2024 |

### Sefer Sikligi (Hafta ici - Tarife 1)

| Saat Dilimi | Sefer Sayisi | Frekans |
|-------------|-------------|---------|
| 05:00-06:00 | 6 | ~10 dk aralik |
| 06:00-07:00 | 36 | ~1.7 dk aralik (rush) |
| 07:00-08:00 | 42 | ~1.4 dk aralik (peak rush) |
| 08:00-09:00 | 30 | ~2 dk aralik |
| 09:00-17:00 | 240 | ~2 dk aralik (gun ortasi) |
| 17:00-18:00 | 30 | ~2 dk aralik |
| 18:00-21:00 | 72 | ~2.5 dk aralik |
| 21:00-00:00 | 54 | ~3.3 dk aralik |

Ilk sefer: 05:50 | Son sefer: 23:50

---

## 4. Durak Bilgileri

### Direction 0: Cengizhan → Halkapinar Metro (32 durak, ~40 dk)

| Seq | Durak Adi | Enlem | Boylam |
|-----|-----------|-------|--------|
| 1 | Cengizhan Son Durak | 38.4772 | 27.1690 |
| 2 | Borsa Okulu Eski Sondurak | 38.4768 | 27.1699 |
| 3 | Yesil Ulu Cami | 38.4754 | 27.1669 |
| 4 | Yasemin | 38.4767 | 27.1638 |
| 5 | Saglik Ocagi | 38.4766 | 27.1596 |
| 6 | Cengizhan 75. Yil Lisesi | 38.4753 | 27.1579 |
| 7 | 75. Yil Parki | 38.4740 | 27.1567 |
| 8 | Birkent 2 | 38.4729 | 27.1571 |
| 9 | Birkent | 38.4729 | 27.1588 |
| 10 | Durmus Yasar Ilkogretim | 38.4725 | 27.1608 |
| 11 | Alpaslan | 38.4713 | 27.1636 |
| 12 | PTT Santral | 38.4699 | 27.1652 |
| 13 | Alparslan Mah. Muhtarlik | 38.4697 | 27.1671 |
| 14 | Tas Ocagi | 38.4684 | 27.1683 |
| 15 | Mavi Kose | 38.4680 | 27.1665 |
| 16 | Adil Akcamli | 38.4670 | 27.1655 |
| 17 | Kopru | 38.4658 | 27.1635 |
| 18 | Bayrakli Camlik | 38.4671 | 27.1611 |
| 19 | Bayrakli Ust Gecit | 38.4641 | 27.1625 |
| 20 | Piyale | 38.4613 | 27.1696 |
| 21 | Smyrna | 38.4604 | 27.1732 |
| 22 | Manas | 38.4579 | 27.1751 |
| 23 | Bayrakli Depo | 38.4559 | 27.1764 |
| 24 | Halide Edip Adivar | 38.4522 | 27.1784 |
| 25 | Adliye | 38.4500 | 27.1796 |
| 26 | Ucuncu Sanayi | 38.4458 | 27.1810 |
| 27 | Bolge Idare Mahkemesi | 38.4432 | 27.1800 |
| 28 | Cinarli Mesleki ve Teknik AL | 38.4408 | 27.1753 |
| 29 | Cinarli Dis Hastanesi | 38.4397 | 27.1734 |
| 30 | Halkapinar Spor Salonu | 38.4353 | 27.1730 |
| 31 | Halkapinar Tramvay | 38.4335 | 27.1704 |
| 32 | Halkapinar Metro | 38.4331 | 27.1693 |

### Direction 1: Halkapinar Metro → Cengizhan (28 durak, ~41 dk)

| Seq | Durak Adi |
|-----|-----------|
| 1 | Halkapinar Metro |
| 2 | Camdibi Saglik Ocagi |
| 3 | Mersinli |
| 4 | Stadyum Istasyon |
| 5 | Bolge Idare Mahkemesi |
| 6 | Ucuncu Sanayi |
| 7 | Adliye |
| 8 | Halide Edip Adivar |
| 9 | Bayrakli Depo |
| 10 | Manas |
| 11 | Smyrna |
| 12 | Matbaa |
| 13 | Yunus Keskin Parki |
| 14 | Adil Akcamli |
| 15 | Mavi Kose |
| 16 | Tas Ocagi |
| 17 | Alparslan Mah. Muhtarlik |
| 18 | PTT Santral |
| 19 | Alpaslan |
| 20 | Durmus Yasar Ilkogretim |
| 21 | Birkent |
| 22 | 75. Yil Parki |
| 23 | Cengizhan 75. Yil Lisesi |
| 24 | Saglik Ocagi |
| 25 | Yasemin |
| 26 | Yesil Ulu Cami |
| 27 | Borsa Okulu Eski Sondurak |
| 28 | Cengizhan Son Durak |

---

## 5. Seyahat Suresi Istatistikleri

### Toplam Seyahat Suresi (Uctan uca)

| Metrik | Deger |
|--------|-------|
| Ortalama | 40.8 dk |
| Medyan | 40.1 dk |
| Std Sapma | 0.7 dk |
| Minimum | 40.1 dk |
| Maksimum | 41.5 dk |

### Duraklar Arasi Seyahat Suresi

| Metrik | Deger |
|--------|-------|
| Ortalama | 1.41 dk |
| Medyan | 1.17 dk |
| Std Sapma | 0.82 dk |
| Minimum | 0.63 dk |
| Maksimum | 5.67 dk |

### Kritik Gozlem

Std sapma sadece 0.7 dk. Bu, GTFS verisinin **planlanmis (scheduled)** zamanlari icerdigini gosteriyor, gercek (real-time) veriyi degil. Bu durum modelleme stratejisini dogrudan etkiler (bkz. Bolum 8).

---

## 6. Spatial (Mekansal) Bilgiler

### Koordinat Kapsami

| Olcum | Min | Max |
|-------|-----|-----|
| Enlem | 38.4331 | 38.4772 |
| Boylam | 27.1560 | 27.1812 |

### Guzergah Noktalari

- Shape 1502 (Gidis): 382 GTFS nokta + 824 CSV nokta
- Shape 2502 (Donus): 333 GTFS nokta + 772 CSV nokta
- CSV guzergah verisi GTFS'ten ~2x daha yuksek cozunurlukte

Rota, Bayrakli bolgesi icinde kuzey-guney yonlu kentsel bir hat. Halkapinar Metro aktarma noktasina baglanti sagliyor.

---

## 7. Bu Rotayi Secme Gerekceleri

| Kriter | Route 502 Degeri | Neden Onemli |
|--------|-----------------|--------------|
| Trip sayisi | 608 | Yeterli egitim verisi |
| Durak sayisi | 32/28 (gidis/donus) | Orta uzunluk - ne cok kisa ne cok uzun |
| Seyahat suresi | ~41 dk | Ideal tahmin araligi |
| Sefer sikligi | Peak saatte 1.4 dk | Yogun veri |
| Veri kapsami | Tum kaynaklarda mevcut | GTFS + CSV entegrasyonu test edilebilir |
| Metro baglantisi | Halkapinar Metro | Duzensiz sefer olasiligi dusuk |
| Kentsel rota | Bayrakli ic hat | Trafik patternleri belirgin |
| 3 tarife | Hafta ici/Cumartesi/Pazar | Gun tipi analizi yapilabilir |

---

## 8. Gercek Zamanli Veri Kaynagi: Izmir Teknoloji API (COZULDU)

### Eski Sorun (Artik Gecersiz)

GTFS stop_times verisi sadece **planlanmis** zamanlari icerir, gercek varis zamanlarini degil.
Std sapma 0.7 dk gibi cok dusuk bir deger olmasi bunu kanitliyordu.

### Cozum: Izmir Teknoloji A.S. Acik Veri API'leri

Izmir Buyuksehir Belediyesi, ESHOT otobusleri icin **gercek zamanli GPS API'leri** sunuyor.
Bu API'ler anonim erisime acik ve JSON formatinda donus yapiyor.

#### Kullanilacak Endpointler

| # | Endpoint | Parametre | Donen Veri |
|---|----------|-----------|------------|
| 1 | `hatotobuskonumlari/{hatId}` | hatId=502 | Hattaki tum otobuslerin anlik GPS konumu (OtobusId, Yon, KoorX, KoorY) |
| 2 | `duragayaklasanotobusler/{durakId}` | durakId | Duraga yaklasan tum otobuslerin listesi (KalanDurakSayisi, konum, hat bilgisi) |
| 3 | `hattinyaklasanotobusleri/{hatId}/{durakId}` | hatId=502, durakId | Belirli hattın belirli duraga yaklasan otobusleri |

Base URL: `https://openapi.izmir.bel.tr/api/iztek/`

#### API Test Sonuclari (26 Mart 2026, 11:07)

- **hatotobuskonumlari/502**: 7 benzersiz otobus, 20 konum kaydi (ayni otobus birden fazla kez)
- **duragayaklasanotobusler/10462** (Halkapinar Metro): 5 yaklasan otobus, kalan durak sayilari: 2, 14, 24, 35, 38
- **hattinyaklasanotobusleri/502/30286** (Manas duragi): 4 yaklasan 502 otobusu

#### Veri Toplama Stratejisi

```
Izmir Teknoloji API (her 30 saniyede sorgu)
    ↓
Otobus GPS konumlari + Duraga yaklasan bilgisi
    ↓
SQLite veritabanina kaydet (bus_positions, stop_arrivals, trip_events)
    ↓
Trip Extractor: Otobus hareketlerinden seferleri tespit et
    ↓
Duraklar arasi GERCEK seyahat sureleri (saniye cinsinden)
    ↓
GTFS planlanmis sureler ile karsilastir → gecikme/sapma hesapla
    ↓
ML-ready dataset (CSV)
```

#### Veri Toplama Scripti

Hazir ve calisiyor: `data_collector/collector.py`

```bash
# Test calistirma (tek API cagri)
python collector.py --test

# Surekli veri toplama (30 sn aralik, Ctrl+C ile durdur)
python collector.py

# 1 saat boyunca 60 sn aralikla topla
python collector.py --interval 60 --duration 3600

# Toplanan veriden trip ve segment CSV'leri cikar
python trip_extractor.py

# Istatistik goster
python trip_extractor.py --stats
```

#### Veritabani Semasi

```
bus_positions         → Her pollingde otobus konumlari (ana tablo)
stop_arrivals         → Kilit duraklara yaklasan otobusler + kalan durak sayisi
trip_events           → Otobuslerin durak gecis olaylari (arrival tespiti)
```

#### Hedef Veri Miktari

| Sure | Tahmini Kayit | Yeterliligi |
|------|--------------|-------------|
| 1 gun | ~20K konum + ~5K yaklasma | İlk prototip icin yeterli |
| 1 hafta | ~140K konum + ~35K yaklasma | Baseline modeller icin yeterli |
| 2-4 hafta | ~500K+ konum + ~140K+ yaklasma | Deep learning icin ideal |
| 6+ hafta | ~1M+ kayit | Makale seviyesi veri hacmi |

#### Makale ile Karsilastirma

| Kriter | Makale (Istanbul) | Bizim Yaklasimimiz (Izmir) |
|--------|------------------|--------------------------|
| Veri kaynagi | IETT GPS sistemi | Izmir Teknoloji Acik API |
| Veri tipi | Gercek GPS | Gercek GPS (ayni kalite) |
| Guncelleme | ? | Her 30 saniye |
| Ek bilgi | Sadece konum | Konum + KalanDurakSayisi |
| Planlama verisi | GTFS | GTFS + CSV (daha zengin) |

### GTFS Verisinin Yeni Rolu

GTFS artik tahmin hedefi degil, **feature** olarak kullanilacak:
- **scheduled_travel_time**: Planlanmis duraklar arasi sure (feature)
- **actual_travel_time**: API'den toplanan gercek sure (target)
- **deviation**: actual - scheduled (alternatif target)

Bu yaklasim makaleye **ozgun katki** sagliyor: makale planlanmis sureyi feature olarak kullanmiyor.

---

## 9. Feature Engineering Plani

### Makale Ozellikleri (Uygulanacak)

| Feature | Kaynak | Aciklama |
|---------|--------|----------|
| stop_sequence | stop_times.txt | Durak sirasi |
| direction_id | trips.txt | Gidis/donus yonu |
| route_id | trips.txt | Hat ID (genel modelde) |
| hour_of_day | stop_times.txt | Saat dilimi |
| day_type | calendar.txt | Hafta ici / Cumartesi / Pazar |
| weather_* | Harici API | Sicaklik, yagis, nem |
| time_block | Turetilecek | Sabah rush / gun ortasi / aksam rush / gece |

### Ozgun Ozellikler (Makalede Yok - Bizim Katki)

| Feature | Kaynak | Aciklama |
|---------|--------|----------|
| scheduled_travel_time | stop_times.txt | Planlanmis duraklar arasi sure |
| cumulative_scheduled_time | stop_times.txt | Baslangictan itibaren kumulatif sure |
| distance_to_next_stop | shapes.txt + guzergah CSV | GPS mesafesi |
| route_segment_complexity | guzergah CSV | Donus/viraj yogunlugu |
| stop_density | stops.txt | Bolgedeki durak yogunlugu |
| is_transfer_stop | Meta | Aktarma noktasi mi (Halkapinar Metro) |
| frequency_at_hour | hareketsaatleri.csv | O saatte kac sefer var |

### Hedef Degisken (Target)

```
y = duraklar_arasi_gercek_seyahat_suresi (dakika)
    → API'den toplanan veriden hesaplanir

Alternatif target:
y = gecikme = gercek_sure - planlanmis_sure (dakika)
    → Sapmaya odakli tahmin
```

---

## 10. Model Gelistirme Plani

### Faz 0: Veri Toplama (Hafta 1 - paralel baslat)

```
Adim 1: collector.py'yi arka planda baslatip surekli calistir
Adim 2: Ilk gun sonunda trip_extractor.py ile veri kalitesini dogrula
Adim 3: Hava durumu verisini paralel topla (OpenWeatherMap)
Adim 4: 1 hafta sonunda ilk analiz: kac trip, kac segment, veri kalitesi
```

> ONEMLI: Collector Hafta 1 basinda baslatilmali ve proje boyunca calismaya
> devam etmeli. Model gelistirme bu sirada paralel ilerler.

### Faz 1: Baseline (Hafta 1-2)

```
Adim 1: Toplanan gercek veriyi yukle + GTFS ile birlestir
Adim 2: Feature extraction (gercek sure + planlanmis sure + temporal)
Adim 3: Train/Val/Test split (%70/%15/%15, zamana gore)
Adim 4: Baseline modeller
         - Planlanmis sure (naive baseline)
         - Historical ortalama (saat + gun tipi bazli)
         - Linear Regression
         - Random Forest
         - XGBoost
Adim 5: Metrik hesaplama (MAE, MAPE, R2)
```

### Faz 2: Deep Learning (Hafta 3)

```
Adim 1: Sekans verisi hazirlama (sliding window - onceki duraklarin sureleri)
Adim 2: LSTM modeli (makale ile ayni mimari)
Adim 3: GRU modeli
Adim 4: Transformer modeli (basit)
Adim 5: Hiperparametre araması
```

### Faz 3: Hibrit Model (Hafta 4)

```
Adim 1: Selective trend mekanizmasi (N<1000 icin)
Adim 2: Context-aware features (hava durumu, gun tipi, saat blogu)
Adim 3: Ensemble / stacking
Adim 4: SHAP analizi (feature importance)
```

### Faz 4: Genellestirme (Hafta 5+)

```
Adim 1: Collector'a baska rotalari ekle (599, 585, 268, 171)
Adim 2: Genel model egitimi (route_id feature olarak)
Adim 3: Route-level vs General model karsilastirmasi
Adim 4: Condition-based degerlendirme (hava, saat, gun)
```

---

## 11. Beklenen Performans Hedefleri

### Route 502 (Pilot)

| Metrik | Baseline | LSTM | Hibrit | Hedef |
|--------|----------|------|--------|-------|
| MAE | ~4-5 dk | ~3 dk | ~2.5 dk | < 2.5 dk |
| MAPE | ~20% | ~15% | ~12% | < 12% |
| R2 | ~0.75 | ~0.90 | ~0.93 | > 0.93 |

### Basari Kriteri

Pilot basarili sayilir eger:
- End-to-end pipeline calisiyor
- En az 3 baseline + 2 DL model egitildi
- MAE < 3.5 dk (tek rota icin)
- Tum rotalara genisletme icin pipeline hazir

---

## 12. Dosya Yapisi Plani

```
bus_arrival/
├── izmir_dataset/              # Ham GTFS + CSV verileri (mevcut)
├── data_collector/             # Gercek zamanli veri toplama (HAZIR)
│   ├── config.py               # Route 502 durak/API konfigurasyonu
│   ├── collector.py            # Ana veri toplama scripti
│   ├── trip_extractor.py       # Toplanan veriden trip/segment cikarma
│   └── collected_data/         # SQLite DB + extracted CSV'ler
│       ├── route_502_realtime.db
│       └── extracted_trips/
│           ├── route_502_segments.csv  (ML icin)
│           └── route_502_trips.csv
├── src/
│   ├── data_processing/
│   │   ├── gtfs_loader.py
│   │   ├── feature_engineering.py
│   │   └── data_merger.py      # GTFS + realtime birlestirme
│   ├── models/
│   │   ├── baselines.py
│   │   ├── lstm_model.py
│   │   ├── gru_model.py
│   │   ├── transformer_model.py
│   │   └── hybrid_model.py
│   ├── evaluation/
│   │   ├── metrics.py
│   │   └── comparison.py
│   └── utils/
│       ├── config.py
│       └── visualization.py
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_baseline_models.ipynb
│   └── 04_deep_learning.ipynb
├── results/
│   ├── figures/
│   └── tables/
└── ROUTE_502_PILOT_PLAN.md
```

---

## 13. Hemen Baslayalim - Ilk Adimlar

### Adim 1: Veri Toplamaya HEMEN Basla (KRITIK)

```bash
cd data_collector/
python collector.py --test              # Ilk test
python collector.py --interval 30       # Surekli topla (arka planda calistir)
```
> Neden acil: Veri toplanmadan model egitilemez. 1 haftalik veri bile
> anlamli sonuclar uretir. Her gecen gun kayip veridir.

### Adim 2: Veri Kalite Kontrolu (1. gun sonu)

```bash
python trip_extractor.py --stats        # Kac kayit toplandi?
python trip_extractor.py                # Trip'leri cikar, CSV olustur
```
- Toplanan konum kaydi sayisi
- Tespit edilen trip sayisi
- Duraklar arasi sure dagilimi mantikli mi?

### Adim 3: GTFS + Realtime Birlestirme (1 hafta sonra)

- Toplanan gercek sureleri GTFS planlanmis surelerle eslestir
- scheduled_travel_time vs actual_travel_time karsilastirmasi
- Feature matrix olustur

### Adim 4: Baseline Modeller

- Planlanmis sure baseline (GTFS scheduled = tahmin)
- Historical ortalama (saat + gun bazli)
- Linear Regression, Random Forest, XGBoost
- Ilk metrikleri raporla (MAE, MAPE, R2)

### Adim 5: LSTM ile Ilk Deep Learning Denemesi

- Sekans verisi hazirla (onceki duraklarin gercek sureleri)
- Basit LSTM egit
- Baseline ile karsilastir
