# Progress

**Son Guncelleme:** 2026-04-28

---

## Tamamlanan Isler

### Asama 0 — Veri Toplama Altyapisi ✅
- [x] Izmir Teknoloji API kesfedildi ve test edildi (anonim erisim, JSON)
- [x] `data_collector/config.py` — Route 502 durak listesi (32 gidis + 28 donus), API endpointleri
- [x] `data_collector/collector.py` — GPS polling (30sn), hava durumu (saatlik), trafik (20dk), SQLite kayit, trip event detection
- [x] OpenWeatherMap entegrasyonu (gercek + mock fallback)
- [x] TomTom Traffic Flow API entegrasyonu (31 segment, congestion_ratio, 20dk aralik)
- [x] Graceful shutdown (SIGINT/SIGTERM), loglama, test modu

### Asama 1 — Ham Veri Cikarma ✅
- [x] `data_collector/trip_extractor.py` — trip_events'ten sefer ve segment cikarma
- [x] CSV export: `route_502_segments.csv`, `route_502_trips.csv`
- [x] Kalite kontrol: travel_minutes aralik filtresi (0.33–15 dk), seq tutarliligi
- [x] Istatistik goruntuleyici (`--stats`)

### Asama 2 — Feature Engineering ✅
- [x] `notebooks/feature_engineering.ipynb`
- [x] Zamansal: hour, day_of_week, is_weekend, time_block
- [x] Mekansal: distance_m (Haversine), stop_progress (0-1)
- [x] GTFS: scheduled_travel_minutes, deviation_minutes (ozgun katki)
- [x] Hava durumu: 7 feature (temperature, humidity, precipitation, wind_speed, visibility, weather_category, is_rainy)
- [x] Cikti: `route_502_features.csv` (27 kolon)

### Asama 3 — Baseline Modeller ✅
- [x] `notebooks/baseline_models.ipynb`
- [x] Naive GTFS (planlanmis sure = tahmin)
- [x] Historical Average (saat x gun_tipi x durak)
- [x] Linear Regression
- [x] Random Forest (100 agac, max_depth=10)
- [x] XGBoost (n_estimators=200, lr=0.05)
- [x] Cikti: `results/tables/baseline_results.csv`

### Asama 4 — Deep Learning ✅
- [x] `notebooks/deep_learning.ipynb`
- [x] Cift girdili LSTM (sequence 128 unit + context Dense 32)
- [x] GRU varyanti
- [x] Sliding window (onceki N durak → sonraki durak seyahat suresi)
- [x] Cikti: model dosyalari (.keras, .pkl) + `results/tables/dl_results.csv`

### Asama 5 — Hibrit Model ✅
- [x] `notebooks/hybrid_model.ipynb`
- [x] Selective Trend mekanizmasi (az verili kombinasyonlar icin GTFS + sapma)
- [x] Enhanced XGBoost (17 feature, deviation_history, schedule_ratio, hour_sin/cos)
- [x] LSTM (sliding window temporal pattern)
- [x] Ridge Stacking meta-model
- [x] SHAP analizi kodu (shap kuruluysa calisir)
- [x] Ablation study: scheduled_travel_minutes ve deviation_history kaldirinca performans dususu kanitlandi
- [x] Cikti: `results/tables/hybrid_results.csv`, `ablation_study.csv`, `all_model_results.csv`

### Asama 6 — Kapsamli Degerlendirme ✅
- [x] `notebooks/evaluation.ipynb`
- [x] Makale karsilastirmasi (Kaya & Kalay IEEE 2025)
- [x] Kosul bazli performans (yon, zaman dilimi, hava durumu, durak pozisyonu)
- [x] Istatistiksel testler (paired t-test, Wilcoxon signed-rank)
- [x] Hata analizi (bias, residual dagilimi)
- [x] Cikti: `results/tables/full_comparison_table.csv`, `statistical_tests.csv`

### Proje Yonetimi ✅
- [x] GTFS statik veri temin edildi (`data/bus-eshot-gtfs/`)
- [x] ESHOT acik veri CSV'leri temin edildi (`data/eshot-otobus-*.csv`)
- [x] Proje dosya yapisi temizlendi ve duzenlendi
- [x] `EXECUTION_PLAN.md` ve `ROUTE_502_PILOT_PLAN.md` guncel

---

## Kalan Isler

### Asama 0b — Veri Toplama Yurutme ⬜ (EN ONCELIKLI)
- [ ] `collector.py --interval 30` baslatilmali (arka planda, surekli)
- [ ] Minimum 1 hafta (~3000 segment) veri toplanmali
- [ ] Ilk gun: `trip_extractor.py --stats` ile kalite kontrolu
- [ ] OpenWeatherMap API key alinmali (opsiyonel ama onerilen)
- [ ] TomTom API key alinmali (`export TOMTOM_API_KEY=...`)

### Asama 3-6 Tekrar — Yeni Veri ile ⬜
- [ ] Yeterli veri toplandiktan sonra tum notebook'lar sirayla tekrar calistirilacak
- [ ] Yeni sonuclarla makale karsilastirmasi guncellenecek
- [ ] Hedef: MAE < 2.5 dk

### Asama 7 — Demo Sistemi ⬜ (OPSIYONEL)
- [ ] `scripts/web_dashboard.py` hibrit modelle entegre edilecek
- [ ] API endpoint: `GET /predict?stop_id=30286&hour=8&day_type=weekday`
- [ ] Route 502 harita gorunumu + anlik otobus konumlari
- [ ] Son 24 saat performans metrikleri

### Asama 8 — Final Rapor ve Sunum ⬜
- [ ] Giris: Problem tanimi, motivasyon
- [ ] Ilgili Calismalar: Makale analizi + literatur
- [ ] Metodoloji: Veri toplama, feature engineering, model mimarisi
- [ ] Sonuclar: Tum metrikler, gorsellestirmeler
- [ ] Ozgun Katkilar: Scheduled time feature, Izmir verisi, GTFS+API hibrit yaklasim
- [ ] Sonuc ve Gelecek Calismalar
- [ ] GTU sunum sablonuyla sunum hazirlanacak

---

## Ilk Test Sonuclari (20 dk / 61 segment — referans)

| Model | MAE (dk) | MAPE (%) | R2 |
|-------|----------|----------|-----|
| Enhanced XGBoost | 0.37 | 21.4 | 0.49 |
| Hybrid Stacking | 0.37 | 21.7 | 0.49 |
| Historical Average | 0.58 | 38.1 | -0.04 |
| Naive (GTFS) | 0.59 | 42.1 | 0.03 |
| Random Forest | 0.61 | 49.5 | 0.05 |
| XGBoost | 0.67 | 51.3 | 0.03 |
| LSTM | 0.95 | 70.0 | -0.33 |
| GRU | 0.97 | 73.9 | -0.42 |

> Bu sonuclar yalnizca pipeline dogrulama icin kullanilmistir. LSTM/GRU az veriyle kotu performans gostermektedir ve 1000+ segment ile iyilesmesi beklenmektedir.

---

## Teslim Kriterleri Durumu

### Minimum Teslim (Gecer Not)
- [x] Calisan veri toplama sistemi
- [x] Trip extractor calisiyor
- [x] Feature engineering pipeline
- [x] 5 baseline model calisiyor
- [ ] En az 1 haftalik gercek veri
- [ ] MAE < 3.5 dakika
- [ ] Kapsamli rapor

### Hedeflenen Teslim (Iyi Not)
- [x] LSTM/GRU modelleri calisiyor
- [x] Hibrit stacking ensemble
- [x] Ablation calismasi
- [x] Istatistiksel anlamlilik testleri
- [ ] MAE < 2.5 dk (yeterli veri ile)
- [ ] Hava durumu feature etkisi kanitlandi

### Mukemmel Teslim (En Iyi Not)
- [x] SHAP analizi kodu hazir
- [ ] Hibrit model MAE < 2.0 dk
- [ ] Calisan demo uygulamasi
- [ ] Akademik yayin taslagi

---

## 2026-04-28 Yonetici Ozeti

### Mevcut Asama
- Proje gelistirme bakimindan ileri seviyede: veri toplama, feature engineering, baseline, deep learning, hibrit model ve degerlendirme zinciri kurulmus.
- Proje teslim bakimindan orta seviyede risk tasiyor: gercek veri hacmi halen yetersiz, final rapor ve demo kapatilmis degil.

### Teknik Durum Degerlendirmesi
1. End-to-end pipeline calisir durumda ve ilk pilot kosuda dogrulanmis.
2. Mevcut performans tablolari sadece kucuk test verisiyle uretilmis oldugu icin nihai sonuc olarak kullanilmamali.
3. LSTM/GRU'nun zayif gorunmesi buyuk olasilikla veri azligindan kaynaklaniyor; bu asamada model degil veri darboğazi belirleyici.
4. GTFS ve trafik/hava baglaminin projeye ozgun katkisi dokumante edilmis ve metodolojik olarak guclu gorunuyor.

### Kritik Riskler
1. Collector'in surekli calisiyor oldugu raporlanmiyor; bu, tum sonraki asamalari bloke ediyor.
2. API key eksikleri nedeniyle hava ve trafik feature'lari gercek operasyon kosullarinda tam olgunlasmamis olabilir.
3. Dokumantasyonda eski notebook/veritabani isimleri bulunuyor; final teslim oncesi terminoloji birlestirilmeli.
4. Final rapor ve sunum henuz baslamadiysa zamanlama riski yuksek.

### Net Karar
- Bu proje "yeniden model tasarlama" asamasinda degil.
- Bu proje "veri toplama operasyonunu stabilize et, sonra tum notebook zincirini yeniden kos" asamasinda.
