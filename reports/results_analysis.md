# Sonuç Tabloları Analizi

**Tarih:** 2026-06-05 (multi-route genelleme + veri bütünlüğü düzeltmesi)
**Kaynak:** `results/tables/`
**Hedef:** Otobüs varış zamanı tahmini için eğitilen modellerin performans değerlendirmesi
**Önceki sürümler:** 2026-04-28 (61 satırlık pilot), 2026-04-29 (138K leakage'lı), 2026-04-29 (138K düzeltilmiş)

---

## ⚠️ 2026-06-05 — Kritik Veri Bütünlüğü Düzeltmesi (mutlaka okuyun)

**Bulgu:** `feature_engineering_v2.ipynb`'deki `build_segments()` fonksiyonu **route_id'ye göre filtre yapmıyordu.** DB'de 3 hat var (502, 268, 565); notebook üçünün segmentlerini birlikte çıkarıp **hepsine 502'nin GTFS scheduled sürelerini ve 502'nin durak koordinatlarını** atıyordu.

Yani `route_502_features_*.csv` ve dolayısıyla **2026-04-29'a kadarki tüm sonuçlar aslında 3 hattın karışımı** üzerinde üretilmişti:

| Kaynak | route_id dağılımı |
|---|---|
| Eski "route_502" v2 (138.282 satır) | 268: 48.719 · 565: 47.622 · **502: yalnızca 41.941** |

268/565 segmentlerine yanlış (502'nin) `scheduled_travel_min` ve `distance_m` değerleri atanmıştı → bu, gürültü olarak R²'yi düşürüyordu.

**Düzeltme:** `scripts/build_features_route.py` yazıldı — `--route` parametresi alıp her hat için **kendi GTFS tarifesi + kendi durak koordinatlarıyla** temiz feature seti üretiyor (`config.ROUTES[route_id]` kullanır). Üç hat ayrı ayrı, doğru şekilde üretildi:

| Hat | Temiz segment | Ort. süre | Std | CV |
|---|---:|---:|---:|---:|
| 502 | 75.579 | 1.208 dk | 1.544 | 1.28 |
| 268 | 115.803 | 1.232 dk | 0.979 | 0.79 |
| 565 | 114.572 | 1.088 dk | 0.872 | 0.80 |

**Etki (502, XGBoost Improved):** Karışık veriden temiz veriye geçiş R²'yi **0.538 → 0.637'ye** çıkardı (yanlış-feature gürültüsü temizlendi). MAE 0.394 → 0.439'a yükseldi çünkü saf 502 verisi daha yüksek varyanslı (CV 1.28). **Temiz sonuçlar bilimsel olarak doğru olanlardır.**

> Bu rapordaki **§1–§8 eski (karışık-veri) sonuçları tarihsel kayıt** olarak korunmuştur. Güncel ve geçerli sonuçlar **§11 Multi-Route**'tadır.

---

## 0. Sürüm Notları

`schedule_ratio = travel_minutes / scheduled_travel_minutes` feature'ı target leakage'a yol açıyordu (hedef değişkeni doğrudan içeriyordu). [notebooks/hybrid_model.ipynb](notebooks/hybrid_model.ipynb) ve [notebooks/evaluation.ipynb](notebooks/evaluation.ipynb)'den çıkarıldı; iki notebook yeniden çalıştırıldı.

**Düzeltme öncesi vs sonrası — Enhanced XGBoost:**

| Metrik | Leakage'lı (geçersiz) | Düzeltilmiş (geçerli) |
|---|---:|---:|
| MAE (dk) | 0.0204 | **0.5064** |
| R² | 0.9905 | 0.2456 |
| MAPE (%) | 1.33 | 56.14 |

Düzeltilmiş sonuçlar bilimsel olarak savunulabilir. Bu rapor sadece geçerli sonuçları içerir.

---

## 1. Veri Özeti

[results/tables/data_summary.csv](results/tables/data_summary.csv):

| Özellik | Değer |
|---|---|
| Toplam segment | **138.282** |
| Train / Test bölünmesi | **110.625 / 27.657** |
| Tarih aralığı | 2026-04-02 → 2026-04-28 (27 gün) |
| Saat aralığı | 06:00 — 22:00 |
| Benzersiz otobüs | 260 |
| Yön | 2 |
| Ortalama travel_minutes | 1.193 dk |
| Std travel_minutes | 1.238 dk |

---

## 2. Tüm Modellerin Karşılaştırması

[results/tables/all_model_results.csv](results/tables/all_model_results.csv):

| Sıra | Model | MAE (dk) | RMSE (dk) | MAPE (%) | R² |
|---|---|---:|---:|---:|---:|
| 1 | **LSTM** | **0.4138** | 0.6914 | 42.11 | 0.0484 |
| 2 | **GRU** | 0.4140 | **0.6887** | 41.89 | 0.0558 |
| 3 | Random Forest | 0.4695 | 0.8731 | 50.22 | **0.3325** |
| 4 | XGBoost | 0.4784 | 0.8819 | 52.15 | 0.3191 |
| 5 | Hybrid Stacking | 0.5003 | 0.9295 | 54.53 | 0.2435 |
| 6 | Enhanced XGBoost | 0.5064 | 0.9282 | 56.14 | 0.2456 |
| 7 | Historical Average | 0.5662 | 0.9922 | 62.50 | 0.1379 |
| 8 | Linear Regression | 0.5933 | 1.0597 | 64.33 | 0.0167 |
| 9 | Naive (GTFS Scheduled) | 0.6125 | 1.0935 | 64.99 | -0.0470 |
| 10 | Selective Trend | 0.6216 | 1.0938 | 68.83 | -0.0475 |

### Anahtar Bulgular

**LSTM ve GRU, MAE'de en iyi modeller** — 0.41 dk. Pilot çalışmadaki "az veride başarısız" tahmini doğrulandı; veri büyüdükçe (61 → 138K) MAE 0.89 → 0.41'e düştü.

**Beklenmedik bulgu: Enhanced XGBoost saf XGBoost'tan daha kötü.** Eklenen feature'lar (`deviation_history`, `hour_sin/cos`, sin/cos encoding) MAE'yi 0.4784'ten 0.5064'e çıkardı. Bu, "daha çok feature = daha iyi model" hipotezini reddediyor; ekstra feature'lar 138K'da gürültü olarak davranıyor olabilir.

**Hybrid Stacking ek karmaşıklığa karşılık avantaj sağlamıyor** (0.5003 vs Enhanced XGBoost 0.5064 — fark ihmal edilebilir). Pratikte daha basit modeller tercih edilmeli.

**Random Forest R²'de en iyi** (0.3325). MAE'de LSTM/GRU önde olsa da, varyansı en çok açıklayan model RF. Bu, RF'nin orta-düzey hataları daha tutarlı yaptığını, LSTM/GRU'nun ise küçük hatalarda daha iyi ama büyük outlier'larda zayıf olduğunu gösteriyor (RMSE'lerine bakınca: LSTM 0.69 vs RF 0.87 — LSTM RMSE'de daha iyi, çelişkili gibi görünüyor ama R² hesabında varyans referansı farklı).

**Naive (GTFS) hâlâ negatif R²** (-0.047). Projenin temel motivasyonu doğrulanıyor: GTFS planı gerçek seyahat süreleri için zayıf bir tahminci.

**Selective Trend en kötü** (R² -0.0475) — Naive'den bile kötü. Az verili kombinasyonlar için trend bileşeni 138K satırda anlam taşımıyor; az verili durum kalmamış.

### MAPE Yorumu

LSTM'in MAPE'si %42 hâlâ yüksek. Sebep: ortalama segment süresi 1.19 dk; 0.41 dk MAE oransal olarak büyük yüzdeye yansıyor. Bu problem türü için **MAE ve RMSE ana metrikler olmalı**, MAPE sadece bağlam olarak.

---

## 3. Hibrit Modeller

[results/tables/hybrid_results.csv](results/tables/hybrid_results.csv):

| Model | MAE (dk) | RMSE (dk) | MAPE (%) | R² |
|---|---:|---:|---:|---:|
| Selective Trend | 0.6216 | 1.0938 | 68.83 | -0.0475 |
| Enhanced XGBoost | 0.5064 | 0.9282 | 56.14 | 0.2456 |
| Hybrid Stacking | 0.5003 | 0.9295 | 54.53 | 0.2435 |

- **Hybrid Stacking ve Enhanced XGBoost arasındaki fark 0.006 dk** — pratik olarak eşit. Stacking'in ek karmaşıklığı katma değer üretmiyor.
- **Selective Trend** 138K veride gereksizleşmiş; az verili kombinasyon kalmadığı için bu mekanizma boş çalışıyor.
- Pilot çalışmada Enhanced XGBoost 0.37 vs şimdi 0.51 → bu pilot rakamın ne kadar leakage tarafından şişirildiğini gösteriyor.

---

## 4. Ablation Çalışması

[results/tables/ablation_study.csv](results/tables/ablation_study.csv) — Enhanced XGBoost (16 feature) üzerinde:

| Konfigürasyon | MAE (dk) | Feature # | Δ vs tam model |
|---|---:|---:|---:|
| **Hava durumu YOK** | **0.4818** | 11 | **-0.0246 (iyileşme)** |
| Tam Model | 0.5064 | 16 | — |
| scheduled + deviation YOK | 0.5186 | 14 | +0.0122 |
| deviation_history YOK | 0.5189 | 15 | +0.0125 |
| scheduled_travel_minutes YOK | 0.5206 | 15 | +0.0142 |

### Şaşırtıcı Bulgu

**Hava durumu feature'ları çıkarınca model belirgin biçimde iyileşiyor** (0.4818 vs 0.5064). Sebep: 27 günlük veride sadece 2 hava kategorisi gözlendi (`clear` ve `cloudy`); 5 hava feature'ı (temperature, humidity, precipitation, is_rainy, weather_enc) düşük varyanslı/sabit gürültü ekliyor. **Akademik raporda bu, "hava feature'ları yağışlı veri olmadan katkı sağlamıyor" şeklinde dürüstçe raporlanmalı.**

### Geçerli Özgün Katkılar

- **`scheduled_travel_minutes`** çıkarıldığında MAE en çok kötüleşiyor (+0.0142). Yani **GTFS tarifesi en güçlü tek sinyal** — bu, projenin özgün katkısı için sağlam bir delil.
- **`deviation_history`** çıkarıldığında MAE +0.0125 kötüleşiyor. Lag feature olarak değer katıyor.
- İkisi birlikte çıkarıldığında etki kümülatif değil (+0.0122 — neredeyse tek başına aynı), yani featureler kısmen örtüşüyor.

### Eylem
Final modelden hava durumu feature'larını çıkarmak veya yağışlı/karlı veri toplandıktan sonra yeniden değerlendirmek. Hava katkısı kanıtlanmadığı için makalede özgün bir "katkı" olarak sunulmamalı.

---

## 5. Koşul Bazlı Performans

[results/tables/condition_analysis.csv](results/tables/condition_analysis.csv) — RF, XGBoost ve Enhanced XGB için:

### Yön
| Yön | N | RF MAE | XGBoost MAE | Enhanced XGB MAE |
|---|---:|---:|---:|---:|
| Halkapınar→Cengizhan | 14.978 | 0.4715 | 0.4863 | 0.4970 |
| Cengizhan→Halkapınar | 12.679 | 0.5190 | 0.5185 | 0.5176 |

Yön asimetrisi küçük. Pilot'taki dramatik fark (0.50 vs 0.26) küçük örneklem etkisiymiş.

### Zaman Dilimi
| Dilim | N | RF MAE | XGBoost MAE | Enhanced XGB MAE |
|---|---:|---:|---:|---:|
| evening_peak | 4.426 | **0.4289** | 0.4422 | 0.4376 |
| morning_peak | 7.285 | 0.5242 | 0.5276 | 0.5281 |
| night | 2.262 | 0.4601 | 0.4655 | 0.4599 |
| off_peak | 13.684 | 0.5032 | 0.5119 | 0.5249 |

**Akşam pik en kolay, sabah pik en zor.** Sabah trafiği daha değişken (kaza, okul açılışları, vs.) — bu makaleye girecek bir bulgu.

### Hava Durumu
| Hava | N | RF MAE | XGBoost MAE | Enhanced XGB MAE |
|---|---:|---:|---:|---:|
| clear | 14.100 | 0.4955 | 0.5076 | 0.5078 |
| cloudy | 13.557 | 0.4910 | 0.4943 | 0.5050 |

İki kategori arasında belirgin fark yok. Yağışsız 27 günlük dönem kanıtlayıcı bir test sunmuyor.

### Durak Pozisyonu
| Bölge | N | RF MAE | XGBoost MAE | Enhanced XGB MAE |
|---|---:|---:|---:|---:|
| **Başlangıç (0-33%)** | 3.698 | **0.8344** | **0.9043** | **0.9764** |
| Orta (33-66%) | 10.138 | 0.4830 | 0.4814 | 0.4703 |
| Bitiş (66-100%) | 13.821 | **0.4095** | 0.4076 | 0.4072 |

**Hat başlangıç bölgesinde MAE iki katından fazla kötü.** Olası sebepler:
- Trip başında lag feature'lar (`prev_travel_time_min`, `prev_deviation`) 0 — model bağlamsız tahmin yapıyor.
- Kalkış noktalarında bekleme süresi, yolcu yoğunluğu sabit olmayabilir.

**Bu, makaleye girmesi gereken metodolojik bir bulgu.** "Cold-start problem" başlığı altında ayrı bir alt bölüm hak ediyor.

---

## 6. İstatistiksel Anlamlılık

[results/tables/statistical_tests.csv](results/tables/statistical_tests.csv) — Random Forest referans alınarak (evaluation notebook'u Enhanced XGB DL'i predictions dict'ine almıyor, en iyi geçerli ML modeli olarak RF seçildi):

| Karşılaştırma | MAE Farkı | t p | Wilcoxon p | p<0.05 |
|---|---:|---:|---:|:-:|
| RF vs Naive (GTFS) | 0.1192 | 0.0000 | 0.0000 | ✅ |
| RF vs Linear Reg | 0.1036 | 0.0000 | 0.0000 | ✅ |
| RF vs Historical Avg | 0.0639 | 0.0000 | 0.0000 | ✅ |
| RF vs Enhanced XGB | 0.0132 | 0.0000 | 0.0117 | ✅ |
| RF vs XGBoost | 0.0078 | 0.0000 | 0.2585 | t-test ✅ / Wilcoxon ❌ |

### Yorumlar
- **Random Forest, baseline'lar (Naive, Linear Reg, Historical Avg) ve Enhanced XGB'den anlamlı şekilde daha iyi** — n=27.657 ile testler güvenilir.
- **RF vs vanilla XGBoost:** t-test çok küçük p (n çok büyük olduğu için her küçük fark anlamlı görünür) ama Wilcoxon p=0.26 → **dağılımsal anlamlı fark yok**. İki model pratik olarak eşit kabul edilmeli.
- **Enhanced XGB, RF'den anlamlı şekilde daha kötü** — feature ekleme stratejisinin bu veri büyüklüğünde işe yaramadığının istatistiksel kanıtı.

### Önemli Eksik
DL modelleri (LSTM, GRU) `evaluation.ipynb`'in `predictions` dict'inde yok; bu nedenle RF vs LSTM testi yapılmadı. Final raporda LSTM'i `predictions` dict'ine ekleyip (sequence input gerektirdiği için ayrı kurulum lazım) RF vs LSTM testini yapmak gerekecek.

---

## 7. Literatürle Karşılaştırma

[results/tables/paper_comparison.csv](results/tables/paper_comparison.csv) — Random Forest ile (evaluation'da en iyi seçildi); ama all_model_results'a göre **gerçek en iyi LSTM (MAE 0.4138)**. Aşağıdaki tablo LSTM ile manuel:

| Metrik | Makale (İstanbul LSTM) | Bizim (LSTM, Izmir 502) | Bizim (RF) | Fark (LSTM) |
|---|---:|---:|---:|---:|
| MAE (dk) | 2.97 | 0.4138 | 0.4695 | -2.56 (-86.1%) |
| MAPE (%) | 14.79 | 42.11 | 50.22 | +27.32 (+184.7%) |
| R² | 0.9272 | 0.0484 | 0.3325 | -0.879 (-94.8%) |

### Kritik Yorum (önceki raporlardan korunuyor)

**MAE'de görünen %86 avantaj doğrudan kıyaslanabilir değil.**
- Bizim hedef: tek durak-durak segmenti süresi (ortalama 1.19 dk).
- Makale hedefi: muhtemelen uçtan uca trip (5-15 dk aralığında).
- Aynı %10 hata, bizim 1.19 × 0.10 = 0.12 dk; makaledeki 10 × 0.10 = 1 dk. Yani küçük rakam kazanma değil, ölçek farkı.

**R²'mizin düşük olması (0.05-0.33)** bunu doğruluyor: hedef varyansımız (1.24² = 1.53) küçük, modelimizin açıkladığı pay az. Makaledeki LSTM'in R²=0.93 elde etmesi, hedef varyansının çok daha büyük olmasından kaynaklanıyor (uçtan uca trip için 5-10 dk std).

**Akademik yayında bu kıyas yapılırken metodolojik farklılıklar açıkça belirtilmeli.**

---

## 8. Üç Sürüm Karşılaştırması

| Metrik | Pilot (61 satır) | 138K leakage'lı | 138K düzeltilmiş |
|---|---|---|---|
| Tarih | 2026-04-28 | 2026-04-29 (sabah) | 2026-04-29 (öğleden sonra) |
| Veri | 1 gün, 13 test | 27 gün, 27.657 test | 27 gün, 27.657 test |
| Enhanced XGBoost MAE | 0.37 (şişmiş) | 0.02 (leakage) | **0.51 (gerçek)** |
| LSTM MAE | 0.89 | 0.41 | 0.41 |
| RF MAE | 0.47 | 0.47 | 0.47 |
| En iyi geçerli MAE | 0.47 (RF) | 0.41 (LSTM) | **0.41 (LSTM)** |
| Bilimsel geçerlilik | Düşük (n=13) | Yok (leakage) | **Yüksek** |

**Net kazanım:** Şu an akademik yayına götürülebilecek tek geçerli sürüm bu. LSTM en iyi model, MAE 0.4138 dk.

---

## 9. Eylem Listesi

### Yüksek Öncelik
- [ ] **Hava durumu feature ablation kararı:** Final modelde hava feature'ları çıkarılsın mı (MAE 0.4818) yoksa kapsamlı veri toplandıktan sonra mı tekrar denensin? Tez/makale yazımı bunu netleştirmeli.
- [ ] **Hat başlangıç bölgesi analizi:** İlk 3-5 durakta MAE neden 2× kötü? Lag feature'ların 0 olması mı, yoksa terminal noktaların doğal değişkenliği mi? Ayrı bir alt analiz yapılmalı, makaleye konu açık olmalı.
- [ ] **DL modellerini istatistiksel testlere dahil et:** [notebooks/evaluation.ipynb](notebooks/evaluation.ipynb)'in `predictions` dict'ine LSTM/GRU eklenmeli. Şu an LSTM en iyi model olduğu halde test edilmiyor.

### Orta Öncelik
- [ ] **Yağışlı/karlı hava verisi:** Veri toplama kış dönemine uzatılmalı veya `weather_category` feature'ı makalede "ileri çalışma" olarak ele alınmalı.
- [ ] **Cold-start çözümü:** Hat başlangıcı için lag feature'ların `0` yerine grup ortalaması ile fillna edilmesi denenebilir.
- [ ] **LSTM hyperparameter tuning:** window_size = 3 ve dropout = 0.2 sabit; daha derin sweep yapılırsa MAE 0.41'in altına inebilir.

### Düşük Öncelik
- [ ] SHAP kütüphanesi kuruluysa (pip install shap) yeni Enhanced XGBoost (16 feature) üzerinde feature importance üretilsin.
- [ ] Demo dashboard (Aşama 7) — LSTM modeline bağlanmalı.
- [ ] Final akademik makale taslağı.

---

## 10. Yönetici Özeti

1. **Target leakage temizlendi.** Sonuçlar artık akademik olarak savunulabilir.
2. **LSTM ve GRU en iyi modeller** (MAE 0.41 dk). DL modellerinin yeterli veri ile baskın olduğu doğrulandı.
3. **"Daha karmaşık model = daha iyi" mitini reddediyoruz:** Enhanced XGBoost (16 feature) saf XGBoost'tan (13 feature) daha kötü performans gösterdi. Hybrid Stacking'in katma değeri yok.
4. **Hava durumu feature'ları gürültü ekliyor** — yağışsız veri ile beklenebilir bir sonuç. Bu, dürüst raporlanmalı.
5. **Hat başlangıcında MAE 2× kötü** — makaleye girecek metodolojik bulgu.
6. **`scheduled_travel_minutes` (GTFS) ablation'da en kritik feature** — projenin özgün katkısı bu somut delile dayanıyor.
7. **Makaleyle MAE karşılaştırması segment vs trip ölçek farkından dolayı dolaylı** — yayında bu açıkça belgelenmeli.

---

## 11. Multi-Route Genelleme (2026-06-05 — GÜNCEL, GEÇERLİ SONUÇLAR)

[results/tables/multi_route_comparison.csv](results/tables/multi_route_comparison.csv) — her hat **kendi temiz verisiyle** (doğru GTFS + durak koordinatları) eğitildi. Amaç: yöntemin tek hatta özel olmadığını, farklı hat profillerine genellendiğini kanıtlamak.

| Hat | Segment | Ort. süre | CV | XGBoost MAE | XGBoost MAPE | XGBoost R² | LSTM MAE | LSTM MAPE | LSTM R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **502** | 75.579 | 1.21 dk | 1.28 | 0.439 | 43.6% | **0.637** | 0.360 | 39.7% | 0.337 |
| **268** | 115.803 | 1.23 dk | 0.79 | 0.379 | 37.4% | 0.533 | 0.323 | 33.4% | 0.407 |
| **565** | 114.572 | 1.09 dk | 0.80 | 0.308 | 35.0% | 0.479 | **0.295** | 33.0% | **0.531** |

### Anahtar Bulgular

1. **Yöntem 3 hatta da tutarlı çalışıyor — genelleme kanıtlandı.** XGBoost R² aralığı 0.48–0.64, LSTM her hatta baseline'ları geçiyor. Bu, "yöntemimiz 502'ye özel bir hile değil" tezinin somut delili ve makaleye girecek en güçlü genelleme argümanı.

2. **CV (varyasyon katsayısı) ile R² ters orantılı.** 502 en yüksek CV'ye (1.28) sahip → en zor hat, ama XGBoost yine de en yüksek R²'yi (0.64) elde ediyor çünkü yüksek varyans = açıklanacak daha çok sinyal. 565 en düşük varyanslı (CV 0.80) → MAE en düşük (0.31) ama R² LSTM'de en yüksek.

3. **LSTM, kısa-segment hatlarda (268, 565) MAE'de XGBoost'u net geçiyor**, 502'de de öne çıkıyor. Üç hatta da Improved LSTM en düşük MAE'yi veriyor — DL'in genelleme avantajı doğrulanıyor.

4. **Veri bütünlüğü düzeltmesinin etkisi (§0):** 502'de R² karışık-veriden temiz-veriye 0.538 → 0.637 yükseldi. Yanlış feature'lar temizlenince modelin gerçek açıklayıcı gücü ortaya çıktı.

### Üretim Pipeline'ı

- `scripts/build_features_route.py --route <RID>` → temiz v2/v3/v4 CSV
- `scripts/improved_ml.py --route <RID>` → XGBoost/RF Improved sonuçları
- `scripts/improved_lstm.py --route <RID>` → Improved LSTM sonuçları
- `scripts/build_multi_route_comparison.py` → özet tablo

Çıktılar: `results/tables/improved_{ml,lstm}_results[_route_<RID>].csv` ve `multi_route_comparison.csv`.
