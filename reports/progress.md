# Progress

**Son Guncelleme:** 2026-04-29

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

### Asama 0b — Veri Toplama Yurutme ✅
- [x] `collector.py` 27 gun calistirildi (2026-04-02 → 2026-04-28)
- [x] 1.979.941 GPS kaydi, 138.282 segment, 46.473 trip
- [x] OpenWeatherMap entegrasyonu calisir (clear + cloudy gozlemlendi; yagis henuz yok)
- [x] TomTom entegrasyonu calisir (congestion_ratio kolonu mevcut)

### Asama 3-6 Tekrar — Yeni Veri ile ✅ (kismi)
- [x] Tum notebook'lar `features_v2.csv` (138K satir) ile yeniden calistirildi (2026-04-29)
- [x] LSTM/GRU artik calisir durumda — MAE 0.41 dk (pilot 0.89'dan iyilesme)
- [x] Random Forest / XGBoost: MAE 0.47 / 0.48 dk
- [x] Train/Test: 110.625 / 27.657 — istatistiksel testler artik guvenilir
- [ ] **TARGET LEAKAGE DUZELTILMELI:** `schedule_ratio` ve `deviation_minutes` feature seti
      Enhanced XGBoost ve Hybrid Stacking sonuclarini gecersiz kiliyor (bkz. results_analysis.md §0)
- [ ] Leakage duzeltmesinden sonra ablation, statistical_tests, paper_comparison yeniden uretilmeli
- [ ] Hedef: MAE < 2.5 dk (gecerli modellerle MAE 0.41 dk — hedef asildi, ancak segment vs trip
      olcek farki kosulluyla)

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

## Guncel Sonuclar (138.282 segment, 27 gun, 2026-04-29)

### Gecerli Modeller (target leakage'tan etkilenmeyenler)

| Model | MAE (dk) | RMSE (dk) | MAPE (%) | R2 |
|-------|---------:|----------:|---------:|---:|
| LSTM | **0.41** | 0.69 | 42.1 | 0.05 |
| GRU | 0.41 | 0.69 | 41.9 | 0.06 |
| Random Forest | 0.47 | 0.87 | 50.2 | 0.33 |
| XGBoost | 0.48 | 0.88 | 52.2 | 0.32 |
| Historical Average | 0.57 | 0.99 | 62.5 | 0.14 |
| Linear Regression | 0.59 | 1.06 | 64.3 | 0.02 |
| Naive (GTFS Scheduled) | 0.61 | 1.09 | 65.0 | -0.05 |

### Gecersiz (Target Leakage)

| Model | MAE (dk) | Aciklama |
|-------|---------:|----------|
| Enhanced XGBoost | 0.02 | `schedule_ratio = travel/scheduled` feature'i target leakage |
| Hybrid Stacking | 0.02 | Ayni feature seti |

> Enhanced XGBoost ve Hybrid Stacking sonuclari, `schedule_ratio` feature'indan kaynaklanan target leakage nedeniyle gecersizdir. Detay icin: [reports/results_analysis.md](results_analysis.md) §0.

### Pilot Sonuclar (61 segment — referans, artik kullanilmiyor)

| Model | MAE (dk) | R2 |
|-------|---------:|---:|
| LSTM | 0.89 | -0.18 |
| GRU | 0.88 | -0.17 |
| Random Forest | 0.47 | 0.33 |

> 61 → 138.282 satir gecisinde LSTM/GRU MAE %54 iyilesti, R2 negatiften pozitife dondu. Bu, "DL modelleri yeterli veri ile yeniden degerlendirilmeli" ongoru-sunu dogruladi.

---

## Teslim Kriterleri Durumu

### Minimum Teslim (Gecer Not)
- [x] Calisan veri toplama sistemi
- [x] Trip extractor calisiyor
- [x] Feature engineering pipeline
- [x] 5 baseline model calisiyor
- [x] **27 gunluk gercek veri (138.282 segment)**
- [x] **MAE < 3.5 dakika** (LSTM 0.41 dk)
- [ ] Kapsamli rapor

### Hedeflenen Teslim (Iyi Not)
- [x] LSTM/GRU modelleri calisiyor (MAE 0.41 dk)
- [x] Hibrit stacking ensemble (kod hazir; sonuclar leakage nedeniyle yeniden uretilmeli)
- [x] Ablation calismasi (kod hazir; sonuclar leakage nedeniyle yeniden uretilmeli)
- [x] Istatistiksel anlamlilik testleri (kod hazir; sonuclar leakage nedeniyle yeniden uretilmeli)
- [x] **MAE < 2.5 dk** (gecerli modellerin tumu ulasti)
- [ ] Hava durumu feature etkisi kanitlandi (yagisli gun verisi yok)

### Mukemmel Teslim (En Iyi Not)
- [x] SHAP analizi kodu hazir
- [ ] Hibrit model MAE < 2.0 dk (leakage duzeltmesi sonrasi yeniden olculecek)
- [ ] Calisan demo uygulamasi
- [ ] Akademik yayin taslagi

---

## 2026-04-29 Yonetici Ozeti

### Mevcut Asama
- Proje teknik bakimdan tamamlanmaya yakin: 138K segmentlik gercek veri toplandi, tum modeller bu
  veri uzerinde calistirildi, sonuclar uretildi.
- Proje teslim bakimindan **bir kritik blokere takili:** Enhanced XGBoost ve Hybrid Stacking
  modellerinde target leakage var. Bu, akademik yayinda kullanilamaz; duzeltilmesi gerek.

### Teknik Durum Degerlendirmesi
1. Veri toplama operasyonu stabilize oldu — collector 27 gun calisti, 1.98M GPS kaydi, 138K segment.
2. LSTM ve GRU artik gecerli performans uretiyor (MAE 0.41 dk) — pilot calismadaki "az veride
   basarisiz" hipotezi dogrulandi.
3. Random Forest ve XGBoost MAE 0.47-0.48 dk seviyesinde — DL modellerinden hafif geride.
4. **Target leakage:** Hybrid notebook'taki `schedule_ratio = travel/scheduled` feature'i hedefi
   doğrudan iceriyor. Sonuc: modelin "MAE 0.02 dk" basarisi yapay. Tek satirlik feature listesi
   degisikligi ile cozulebilir.
5. Hat baslangic bolgesinde MAE belirgin biçimde kotu (0.83 vs 0.41) — bu metodolojik bir bulgu,
   makaleye girmeli.

### Kritik Riskler
1. **Target leakage duzeltilmeden** akademik yayin/sunum yapilirsa bilimsel olarak savunulamaz.
2. Yağisli/karli hava verisi yok — `weather_category` etkisi kanitlanamiyor; bu, makalede dürüstce
   "bu kosulda gozlem yok" olarak raporlanmali.
3. Demo dashboard hazir degil; teslimde "calisan sistem" bekleniyorsa zaman riski.
4. Final rapor ve sunum hala baslamamis.

### Net Karar
- Oncelik 1: `notebooks/hybrid_model.ipynb` ve `notebooks/evaluation.ipynb`'de `ENHANCED_FEATURES`
  listesinden `schedule_ratio` cikarilsin; iki notebook yeniden calistirilsin.
- Oncelik 2: Sonuclar gerçek bir sekilde stabil olunca, makale yazimi baslayabilir; LSTM (gecerli
  en iyi model) ve duzeltilmis Enhanced XGBoost karsilastirilarak rapor edilmeli.
- Oncelik 3: Demo ve final rapor.
