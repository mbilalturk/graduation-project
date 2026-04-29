# Sonuç Tabloları Analizi

**Tarih:** 2026-04-29
**Kaynak:** `results/tables/`
**Hedef:** Otobüs varış zamanı tahmini için eğitilen modellerin performans değerlendirmesi
**Önceki sürüm:** 2026-04-28 (61 satırlık pilot veri ile)

---

## 0. KRİTİK UYARI — Target Leakage Tespit Edildi

Bu çalıştırmada **Enhanced XGBoost ve Hybrid Stacking modelleri target leakage içeriyor.** Sonuçlar tabloda olduğu gibi raporlanmamalıdır.

### Belirti
| Model | MAE (dk) | RMSE (dk) | MAPE (%) | R² |
|---|---:|---:|---:|---:|
| Enhanced XGBoost | **0.0204** | 0.1043 | 1.33 | **0.9905** |
| Hybrid Stacking | 0.0204 | 0.1044 | 1.33 | 0.9905 |

MAE 0.02 dakika ≈ **1.2 saniye**. Bir otobüs segmenti için bu seviyede doğruluk 138K satırla bile gerçekçi değildir; literatürdeki en iyi LSTM modelleri (Kaya & Kalay, 2.97 dk) ile arasındaki fark açıklanabilir değil.

### Kök Neden
[notebooks/hybrid_model.ipynb](notebooks/hybrid_model.ipynb)'in feature mühendisliği aşamasında üretilen `schedule_ratio` feature'ı:

```python
df['schedule_ratio'] = df['travel_minutes'] / df['scheduled_travel_minutes']
```

Bu kolon hedef değişkeni doğrudan içeriyor. Modele verildiğinde:

```
tahmin = schedule_ratio × scheduled_travel_minutes = travel_minutes
```

Yani model tahmin etmek yerine inputtan hedefi yeniden üretiyor. `schedule_ratio`'nun hedef ile korelasyonu **r = 0.903**, ve `schedule_ratio × scheduled_travel_minutes − travel_minutes` farkı **1.8e-15** (kayan nokta sıfırı).

### Etki
- Tüm `Enhanced XGBoost` ve `Hybrid Stacking` sonuçları geçersiz.
- `ablation_study.csv`'deki tüm satırlar geçersiz (hepsi `schedule_ratio` ile çalıştı; "scheduled + deviation YOK" varyantı bile MAE 0.0273 üretiyor çünkü `schedule_ratio` listede kaldı).
- `paper_comparison.csv`'deki "%99 daha iyi" sonucu yanıltıcı; akademik yayında kullanılırsa iddianın geri çevrilmesine yol açar.
- `statistical_tests.csv`'deki tüm p < 0.05 testleri geçersiz baseline ile yapıldığı için anlamsız.

### Düzeltme
[notebooks/hybrid_model.ipynb](notebooks/hybrid_model.ipynb) ve [notebooks/evaluation.ipynb](notebooks/evaluation.ipynb)'de `ENHANCED_FEATURES` listesinden `schedule_ratio` çıkarılmalı. Alternatif: feature türetme adımında `schedule_ratio` formülünden `travel_minutes` referansı kaldırılmalı (ör. lag versiyonu kullanılmalı: önceki segmentin ratio'su).

`deviation_minutes` (shim'de türetilen `travel - scheduled`) da hedefle r = 0.947 korelasyon göstermekte; bu kolon da feature olarak değil sadece **`deviation_history`'nin türetilmesinde** (lag/expanding mean) kullanılmalı, sonra düşürülmeli.

### Geçerli Olan Modeller
Aşağıdaki 7 model **target leakage'tan etkilenmiyor** — sonuçları güvenilir:

- Naive (GTFS Scheduled) — hiç model kullanmıyor
- Linear Regression — `schedule_ratio` baseline feature setinde değildi
- Random Forest — aynı
- XGBoost (vanilla) — aynı
- Historical Average — sadece grup ortalaması kullanıyor
- LSTM, GRU — sequence input'una `schedule_ratio` dahil değil

Bu modellerin sonuçları aşağıda raporlanan analizin gerçek bilimsel içeriğini oluşturuyor.

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

**Pilot çalıştırmaya göre kazanım:**
- 61 → 138.282 satır (×2267 büyüme)
- 13 → 27.657 test örneği (istatistiksel testler artık güvenilir)
- 1 gün → 27 gün (haftaiçi/haftasonu, peak/off-peak çeşitliliği var)
- 1 saat → 16 saatlik aralık
- 7 → 260 benzersiz otobüs

---

## 2. Geçerli Modellerin Karşılaştırması

Target leakage içermeyen modeller (Enhanced XGBoost ve Hybrid Stacking sonuçları **dahil edilmedi**):

| Sıra | Model | MAE (dk) | RMSE (dk) | MAPE (%) | R² |
|---|---|---:|---:|---:|---:|
| 1 | **LSTM** | **0.4138** | 0.6914 | 42.11 | 0.0484 |
| 2 | **GRU** | 0.4140 | **0.6887** | 41.89 | **0.0558** |
| 3 | Random Forest | 0.4695 | 0.8731 | 50.22 | 0.3325 |
| 4 | XGBoost | 0.4784 | 0.8819 | 52.15 | 0.3191 |
| 5 | Historical Average | 0.5662 | 0.9922 | 62.50 | 0.1379 |
| 6 | Linear Regression | 0.5933 | 1.0597 | 64.33 | 0.0167 |
| 7 | Naive (GTFS Scheduled) | 0.6125 | 1.0935 | 64.99 | -0.0470 |

### Anahtar Bulgular

**LSTM ve GRU artık en iyi modeller.** Pilot çalıştırmada (61 satır) DL modelleri negatif R² ile başarısızdı; 138K satır ile **MAE 0.41 dakikaya** düştüler ve baseline ML modellerini geçtiler. Bu bulgu, [reports/progress.md](reports/progress.md)'deki "DL modelleri yeterli veri ile yeniden değerlendirilmeli" notunu doğruluyor.

**Random Forest ve XGBoost**, MAE bakımından LSTM/GRU'nun arkasında ama R² (0.33 ve 0.32) daha yüksek. RMSE'leri DL modellerinden daha kötü (0.87 vs 0.69) → ML modelleri büyük outlier'larda DL'den daha kötü performans gösteriyor.

**Naive (GTFS) hâlâ en kötü** ve negatif R² üretiyor (R² = -0.047). Bu, projenin temel motivasyonunu doğruluyor: GTFS planlanmış süreleri gerçek seyahat süreleri için zayıf bir tahminci.

**Linear Regression neredeyse Naive seviyesinde** (R² = 0.0167) — problem doğrusal değil, bunu pilot çalıştırmadan bu yana koruyoruz.

### MAPE Yorumu
LSTM/GRU MAPE değerleri (~%42) hâlâ yüksek. Sebep: ortalama segment süresi 1.19 dk; küçük mutlak hata bile yüzdeye yansıyınca büyük görünür. MAPE bu problem türü için yanıltıcı bir metriktir; **MAE ve RMSE'ye odaklanılmalı.**

---

## 3. Koşul Bazlı Performans (Geçerli ML Modelleri)

[results/tables/condition_analysis.csv](results/tables/condition_analysis.csv) — Enhanced XGB sütunu leakage nedeniyle yorumlanmıyor; Random Forest ve XGBoost geçerli:

### Yön
| Yön | N | RF MAE | XGBoost MAE |
|---|---:|---:|---:|
| Halkapınar→Cengizhan | 14.978 | 0.4715 | 0.4863 |
| Cengizhan→Halkapınar | 12.679 | 0.5190 | 0.5185 |

İki yön arasında belirgin asimetri yok; pilot çalışmadaki büyük farklar (0.50 vs 0.26) küçük örneklem etkisiymiş.

### Zaman Dilimi
| Dilim | N | RF MAE | XGBoost MAE |
|---|---:|---:|---:|
| evening_peak | 4.426 | 0.4289 | 0.4422 |
| morning_peak | 7.285 | 0.5242 | 0.5276 |
| night | 2.262 | 0.4601 | 0.4655 |
| off_peak | 13.684 | 0.5032 | 0.5119 |

**Şaşırtıcı bulgu:** Akşam pik saatleri (evening_peak) en kolay tahmin edilen dilim. Sabah pik en zor. Bu, sabah trafik desenlerinin daha değişken olduğunu gösterebilir; tek bir trafik olayı (kaza, vs.) tüm sabah peak'i bozuyor olabilir.

### Hava Durumu
| Hava | N | RF MAE | XGBoost MAE |
|---|---:|---:|---:|
| clear | 14.100 | 0.4955 | 0.5076 |
| cloudy | 13.557 | 0.4910 | 0.4943 |

Sadece iki hava kategorisi gözlemlendi (27 gün boyunca yağış olmamış veya kaydedilmemiş). `rainy` ve `snowy` koşullarında performans bilinmiyor.

### Durak Pozisyonu
| Bölge | N | RF MAE | XGBoost MAE |
|---|---:|---:|---:|
| Başlangıç (0-33%) | 3.698 | **0.8344** | **0.9043** |
| Orta (33-66%) | 10.138 | 0.4830 | 0.4814 |
| Bitiş (66-100%) | 13.821 | **0.4095** | 0.4076 |

**Önemli bulgu:** Hat başlangıcında MAE neredeyse **2 kat** daha kötü. Olası sebep: trip başında `prev_travel_time_min` ve `prev_deviation` lag feature'ları 0 (geçmiş yok); model erken duraklar için gereken bilgiden yoksun. **Bu, makaleye rapor edilmesi gereken metodolojik bir bulgu.**

---

## 4. İstatistiksel Anlamlılık

[results/tables/statistical_tests.csv](results/tables/statistical_tests.csv) — Enhanced XGB referans alınarak yapılmış; **leakage nedeniyle tüm p-değerleri geçersiz.** Düzeltilmiş model ile yeniden çalıştırılmalı.

İlerideki iş için: 27.657 test örneği ile artık **t-test ve Wilcoxon güvenilir**, n=13'teki Tip II hata problemi ortadan kalktı.

---

## 5. Ablation Çalışması

[results/tables/ablation_study.csv](results/tables/ablation_study.csv) — **tüm satırlar leakage altında çalıştırıldığı için yorumlanamaz.** Düzeltilmiş feature seti ile yeniden çalıştırılmalı.

Pilot ablation'da `scheduled_travel_minutes` kaldırılınca MAE en çok kötüleşmişti (özgün katkı kanıtı). Bu testin leakage olmayan versiyonu yapılırsa şu hipotezler test edilebilir:
- `scheduled_travel_minutes` (lag değil, current segment için planlı süre — bu geçerli) etkisi
- `deviation_history` (lag, geçerli) etkisi
- `prev_travel_time_min` (lag, geçerli) etkisi
- Hava durumu feature'larının etkisi

---

## 6. Literatürle Karşılaştırma

[results/tables/paper_comparison.csv](results/tables/paper_comparison.csv) **leakage altındaki Enhanced XGBoost ile yapılmış**, geçersiz.

Geçerli modellerle (LSTM en iyimiz olduğundan) revizyon:

| Metrik | Makale (İstanbul LSTM) | Bizim (LSTM, Izmir 502) | Fark |
|---|---:|---:|---:|
| MAE (dk) | 2.97 | 0.4138 | -2.56 (-86.1%) |
| MAPE (%) | 14.79 | 42.11 | +27.32 (+184.7%) |
| R² | 0.9272 | 0.0484 | -0.879 (-94.8%) |

### Kritik Yorum

MAE'de görünen %86'lık avantaj **doğrudan kıyaslanabilir değildir**:

- **Bizim hedef:** Tek bir durak-durak segmenti süresi (ortalama 1.19 dk).
- **Makale hedefi:** Muhtemelen uçtan uca trip veya çok-segment toplamı (ortalama büyük ihtimalle 5-15 dk).
- Aynı %10 hata, bizim 1.19 dk × 0.10 = 0.12 dk = 0.41 dk MAE'mizden çok daha küçük olur.

R²'nin makaleye göre çok düşük olması (0.05 vs 0.93) bunu doğruluyor: bizim hedef varyansımız (1.24² = 1.53) küçük ve modelin açıkladığı pay az. Makaledeki LSTM'nin R²=0.93 elde etmesi, hedef varyansının çok daha büyük olmasından (uçtan uca trip için 5-10 dk std).

**Akademik yayında bu kıyas yapılırken metodolojik farklılıklar açıkça belirtilmeli, aksi halde yanıltıcı olur.** Pilot çalışmadaki bu uyarı geçerliliğini koruyor.

---

## 7. Önceki Sürümle Karşılaştırma

| Metrik | Pilot (61 satır, 2026-04-28) | Bu çalıştırma (138K satır, 2026-04-29) |
|---|---|---|
| Veri tarih aralığı | 2026-03-26 (1 gün) | 2026-04-02 → 2026-04-28 (27 gün) |
| Train / Test | 48 / 13 | 110.625 / 27.657 |
| En iyi geçerli MAE | 0.47 (RF) | 0.41 (LSTM) |
| LSTM/GRU R² | -0.18 / -0.17 | 0.05 / 0.06 |
| LSTM/GRU MAE | 0.89 / 0.88 | **0.41 / 0.41** |
| İstatistiksel test gücü | n=13, Tip II riski yüksek | n=27.657, güvenilir |
| Hava durumu çeşitliliği | sadece `clear` | `clear` + `cloudy` |
| Zaman dilimi çeşitliliği | sadece `off_peak` | 4 dilim hepsi |
| Hat pozisyonu analizi | sadece başlangıç (0-33%) | 3 bölge tamamı |

**Net kazanım:** DL modelleri artık çalışıyor, koşul bazlı analizler anlamlı, istatistiksel testler güvenilir.

---

## 8. Eylem Listesi

### En Yüksek Öncelik (Yayın için Bloke Eden)
- [ ] **Target leakage düzeltmesi:** [notebooks/hybrid_model.ipynb](notebooks/hybrid_model.ipynb) ve [notebooks/evaluation.ipynb](notebooks/evaluation.ipynb)'de `ENHANCED_FEATURES` listesinden `schedule_ratio` çıkar. `deviation_minutes`'i de feature olarak verme (sadece türetme aracı kalsın).
- [ ] Düzeltme sonrası `hybrid_model.ipynb` ve `evaluation.ipynb` yeniden çalıştırılsın.
- [ ] `ablation_study.csv` ve `statistical_tests.csv` leakage olmadan yeniden üretilsin.

### Orta Öncelik
- [ ] **Hat başlangıç bölgesi analizi:** İlk 1-3 durakta MAE neden 2× kötü? Cold-start (lag yok) etkisi mi, yoksa terminal durakların doğası mı? Ayrı bir alt analiz yapılmalı.
- [ ] **Yağışlı/karlı hava verisi yok** — 27 günde yağış olmamış. Veri toplama daha uzun sürmeli (kış mevsimi dahil) veya `weather_category`'nin makaleye katkısı zayıf raporlanmalı.
- [ ] LSTM/GRU sequence boyutu ve regularization tuning — şu anda window_size=3 ve dropout=0.2.

### Düşük Öncelik
- [ ] SHAP kütüphanesi kuruldu mu kontrol et (`pip install shap`); kuruluysa düzeltilmiş Enhanced XGBoost üzerinde feature importance üretilsin.
- [ ] Demo dashboard (Aşama 7) — leakage düzeltmesinden sonra güncel modelle entegre edilmeli.

---

## 9. Yönetici Özeti

1. **138K satırlık veri ile pipeline'ın çalışabildiği doğrulandı.** Bu büyük bir teslim kazanımı.
2. **Enhanced XGBoost ve Hybrid Stacking sonuçları geçersiz** — `schedule_ratio` üzerinden target leakage var. Düzeltme tek satırlık feature listesi değişikliği; sonra ilgili notebook'lar yeniden koşturulmalı.
3. **LSTM ve GRU artık en iyi geçerli modeller** (MAE 0.41 dk). DL modellerinin "az veride başarısız" ön bulgusu doğrulandı; veri ile birlikte iyileştiler.
4. **Hat başlangıcında MAE belirgin biçimde kötü** — bu makaleye girmesi gereken metodolojik bir bulgu.
5. **Makale ile MAE karşılaştırması doğrudan değil** — ölçek (segment vs trip) farkı belirgin biçimde belgelenmeli.
6. Veri çeşitliliği genişledi ama hâlâ eksik: sadece 2 hava kategorisi (yağışsız), Nisan ayı sıcaklıkları, weekend/weekday dengesi denetlenmedi.
