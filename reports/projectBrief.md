# Project Brief

## Proje Tanimi

**Proje Adi:** Bagiam Duyarli Derin Ogrenme ile Otobus Varis Suresi Tahmini
**Universite:** Gebze Teknik Universitesi (GTU) — CSE496 Bitirme Projesi
**Referans Makale:** Kaya & Kalay, "Spatio-Temporal Forecasting of Bus Arrival Times Using Context-Aware Deep Learning Models in Urban Transit Systems", IEEE Access 2025

**Ozet:** Izmir ESHOT Route 502 (Cengizhan - Halkapinar Metro) hatti uzerinde, gercek zamanli GPS verisi ve GTFS planlanmis zaman verisi kullanarak, duraklar arasi otobus varis surelerini tahmin eden bir makine ogrenmesi sistemi gelistirilmektedir. Projenin ozgun katkisi, GTFS scheduled time'i bir feature olarak kullanmak ve Izmir ozelinde gercek zamanli veriyle calisarak makale sonuclarini (MAE: 2.97 dk) gecmeyi hedeflemektir.

---

## Hedef Kitle

- **Birincil:** GTU bilgisayar muhendisligi bitirme juri heyeti
- **Ikincil:** Izmir Buyuksehir Belediyesi / ESHOT — toplu tasima planlayicilari
- **Ucuncul:** Akademik topluluk — benzer spatio-temporal tahmin problemleri uzerinde calisan arastirmacilar

---

## Temel Hedefler

| Hedef | Metrik | Durum |
|-------|--------|-------|
| Makaleyi gecmek | MAE < 2.5 dk (makale: 2.97 dk) | Yeterli veri ile test edilecek |
| End-to-end pipeline | Veri toplama → Model → Tahmin | Calisiyor |
| Ozgun katki | GTFS scheduled time + deviation feature | Kanıtlandi (ablation) |
| Gercek zamanli veri | Izmir Teknoloji API entegrasyonu | Calisiyor |

---

## Ust Seviye Mimari

```
[Izmir Teknoloji API]          [OpenWeatherMap API]
  (GPS, her 30sn)                (hava, saatlik)
        |                              |
        v                              v
  +-----------+                 +-----------+
  | collector |---------------->|  SQLite   |
  |   .py     |                 |    DB     |
  +-----------+                 +-----------+
                                      |
                                      v
                              +--------------+
                              | trip_extractor|
                              |     .py      |
                              +--------------+
                                      |
                                      v
                              +----------------+
                              | Feature Eng.   |
                              | (notebook)     |
                              +----------------+
                                      |
                    +-----------------+-----------------+
                    |                 |                 |
                    v                 v                 v
             +-----------+   +-------------+   +------------+
             | Baseline  |   | LSTM / GRU  |   | Hybrid     |
             | Models    |   | Deep Learn. |   | Stacking   |
             +-----------+   +-------------+   +------------+
                    |                 |                 |
                    v                 v                 v
              +------------------------------------------+
              |        Evaluation & Comparison           |
              |  (makale karsilastirma, stat. testler)   |
              +------------------------------------------+
                                      |
                                      v
                              +----------------+
                              | Web Dashboard  |
                              | (Flask, todo)  |
                              +----------------+
```

---

## Mevcut Ozellikler

1. **Veri Toplama Sistemi** — ESHOT GPS API'den 30sn aralikla otobus konum verisi, saatlik hava durumu
2. **Trip Extraction** — GPS olaylarindan sefer ve segment tespiti, CSV export
3. **Feature Engineering** — 27 kolonlu ML-ready dataset (zamansal, mekansal, GTFS, hava durumu)
4. **5 Baseline Model** — Naive GTFS, Historical Average, Linear Regression, Random Forest, XGBoost
5. **Deep Learning** — Cift girdili LSTM/GRU (sequence + context branch, 128 unit)
6. **Hibrit Stacking Ensemble** — Selective Trend + Enhanced XGBoost + LSTM + Ridge Meta-Model
7. **SHAP Analizi** — Feature importance kaniti
8. **Ablation Study** — scheduled_travel_minutes ve deviation_history katkisi kaniti
9. **Kapsamli Degerlendirme** — Makale karsilastirmasi, istatistiksel testler, kosul bazli analiz

---

## Proje Durumu

**Pipeline tamamen calisir durumda.** 20 dakikalik test verisiyle (61 segment) dogrulanmistir. Su an yapilmasi gereken: daha fazla gercek veri toplamak (hedef: 1+ hafta) ve notebook'lari yeniden calistirmak. Demo sistemi ve final rapor henuz yapilmadi.
