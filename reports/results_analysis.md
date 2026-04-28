# Sonuç Tabloları Analizi

**Tarih:** 2026-04-28
**Kaynak:** `results/tables/`
**Hedef:** Otobüs varış zamanı tahmini için eğitilen modellerin performans değerlendirmesi

---

## 1. Veri Özeti

Modellerin değerlendirildiği veri kümesi oldukça sınırlıdır:

| Özellik | Değer |
|---|---|
| Toplam segment | 61 |
| Train / Test bölünmesi | 48 / 13 |
| Tarih aralığı | 2026-03-26 (tek gün) |
| Saat aralığı | 14:00 — 14:00 (tek saat) |
| Benzersiz otobüs | 7 |
| Yön | 2 |
| Ortalama travel_minutes | 1.29 dk |
| Std travel_minutes | 0.909 dk |

**Kritik gözlem:** Veri tek bir günde, dar bir saat aralığında ve sadece 13 test örneği üzerinde toplanmış. Bu durum:
- İstatistiksel testlerin gücünü düşürür (t-test/Wilcoxon n=13)
- Modellerin genelleme kapasitesini sorgulanır kılar
- Hava durumu ve zaman dilimi çeşitliliği yetersiz (yalnız `clear` ve `off_peak`)

---

## 2. Genel Model Karşılaştırması

`all_model_results.csv` üzerinden tüm modellerin sıralaması (MAE'ye göre):

| Sıra | Model | MAE (dk) | RMSE (dk) | MAPE (%) | R² |
|---|---|---:|---:|---:|---:|
| 1 | **Enhanced XGBoost** | **0.3694** | 0.6005 | **21.38** | 0.4885 |
| 2 | Hybrid Stacking | 0.3703 | **0.5997** | 21.66 | **0.4897** |
| 3 | Random Forest | 0.4695 | 0.8731 | 50.22 | 0.3325 |
| 4 | XGBoost | 0.4784 | 0.8819 | 52.15 | 0.3191 |
| 5 | Historical Average | 0.5662 | 0.9922 | 62.50 | 0.1379 |
| 6 | Linear Regression | 0.5933 | 1.0597 | 64.33 | 0.0167 |
| 7 | Naive (GTFS) | 0.6125 | 1.0935 | 64.99 | -0.0470 |
| 8 | Selective Trend | 0.6650 | 0.8737 | 58.28 | -0.0830 |
| 9 | GRU | 0.8831 | 1.2281 | 66.59 | -0.1658 |
| 10 | LSTM | 0.8880 | 1.2366 | 66.89 | -0.1820 |

### Temel Çıkarımlar
- **Enhanced XGBoost** ve **Hybrid Stacking** açık ara öne çıkıyor; ikisi arasında pratik fark yok (MAE farkı 0.0009 dk ≈ 0.05 saniye).
- Klasik ML modelleri (RF, XGBoost) baseline'ları (Naive, Historical Avg, Linear Reg) belirgin şekilde geçiyor.
- **Derin öğrenme modelleri (LSTM, GRU) en kötü performansı sergiliyor** — negatif R² değerleri, ortalamayı tahmin etmekten bile kötü olduklarını gösteriyor. Bu, küçük veri kümesi (48 örneklik eğitim) için beklenen bir sonuç.
- **Selective Trend** modeli de negatif R² ile başarısız; Naive baseline'ından daha kötü.

---

## 3. Baseline Karşılaştırması

`baseline_results.csv` analizi:

- **Random Forest** baseline grubunun açık lideri (MAE 0.4695).
- **Naive (GTFS Scheduled)** modeli tabloda en altta — GTFS'in tarifedeki süresi gerçek varışla zayıf eşleşiyor; bu, problemin anlamlı olduğunu kanıtlıyor.
- Linear Regression neredeyse Naive seviyesinde (R²=0.0167), problemin doğrusal olmadığını gösteriyor.

---

## 4. Hibrit Modeller

`hybrid_results.csv` analizi:

| Model | MAE | R² |
|---|---:|---:|
| Selective Trend | 0.6650 | -0.083 |
| Enhanced XGBoost | 0.3694 | 0.4885 |
| Hybrid Stacking | 0.3703 | 0.4897 |

- **Hybrid Stacking** RMSE ve R²'de en iyi; **Enhanced XGBoost** MAE ve MAPE'de en iyi.
- Stacking'in ek karmaşıklığa karşılık sağladığı kazanç ihmal edilebilir düzeyde — pratikte **Enhanced XGBoost tercih edilmeli** (daha basit, yorumlanabilir, eşit hızlı).

---

## 5. Derin Öğrenme Modelleri

`dl_results.csv` analizi:

| Model | MAE | R² |
|---|---:|---:|
| LSTM | 0.8880 | -0.182 |
| GRU | 0.8831 | -0.166 |

Her iki model de **negatif R²** üretiyor → train edilen modeller test üzerinde sabit ortalamadan bile kötü tahmin ediyor. Sebep büyük olasılıkla:
- 48 örneklik eğitim seti (sequence modeller için kesinlikle yetersiz)
- Düzenleme/early-stopping zayıf
- Sequence uzunluğu veriye uygun değil

**Tavsiye:** DL modelleri, veri toplama tamamlandıktan sonra (binlerce trip biriktiğinde) tekrar denenmeli; mevcut haliyle raporlanmamalı veya "yetersiz veri" notu ile sunulmalı.

---

## 6. İstatistiksel Anlamlılık

`statistical_tests.csv` üzerinden Enhanced XGBoost'un diğerlerine karşı testleri (n=13):

| Karşılaştırma | MAE Farkı | t p | Wilcoxon p | p<0.05 |
|---|---:|---:|---:|:-:|
| vs Naive (GTFS) | 0.2491 | 0.0060 | 0.0081 | ✅ Evet |
| vs Historical Avg | 0.2294 | 0.0715 | 0.0681 | ❌ Hayır |
| vs Linear Reg | 0.2873 | 0.0378 | 0.0327 | ✅ Evet |
| vs Random Forest | 0.2003 | 0.0635 | 0.1465 | ❌ Hayır |
| vs XGBoost | 0.2013 | 0.0055 | 0.0034 | ✅ Evet |

### Yorumlar
- Enhanced XGBoost, **Naive, Linear Reg ve standart XGBoost'tan istatistiksel olarak anlamlı şekilde daha iyi**.
- **Random Forest ve Historical Average'a karşı fark istatistiksel olarak anlamlı değil** — örneklem büyüklüğü (n=13) düşük olduğu için Tip II hata riski yüksek.
- Bu sonuç, makale yazımında dürüstçe raporlanmalı: "RF'ye karşı üstünlük gözlemlendi ancak istatistiksel anlamlılığa ulaşmadı (p=0.06)".

---

## 7. Ablation Çalışması

`ablation_study.csv` Enhanced XGBoost üzerinde feature gruplarının etkisini ölçüyor:

| Konfigürasyon | MAE | Özellik # |
|---|---:|---:|
| deviation_history YOK | 0.3529 | 16 |
| Hava durumu YOK | 0.3554 | 12 |
| **Tam Model** | **0.3694** | 17 |
| scheduled + deviation YOK | 0.3752 | 15 |
| scheduled_travel_minutes YOK | 0.3957 | 16 |

### Şaşırtıcı Bulgu
**Bazı özelliklerin çıkarılması modeli iyileştiriyor.** `deviation_history` ve `Hava durumu` çıkarıldığında MAE düşüyor. Olası açıklamalar:
- **Overfitting:** 48 örnekle 17 özellik fazla; gürültülü featureler model performansını düşürüyor.
- **Feature kalitesi:** `deviation_history` yeterli geçmiş veri olmadan zayıf sinyal üretiyor.
- **Hava durumu:** Test setinde hava `clear` sabiti olduğu için bu feature öğrenilemez gürültü ekliyor.

### Önemli Featureler
- `scheduled_travel_minutes` çıkarıldığında MAE en çok kötüleşiyor (0.3957) → **GTFS tarifesi en güçlü tek sinyal**.

### Eylem Önerisi
Final modelde feature seçimi yeniden değerlendirilmeli. `deviation_history` ve hava durumu featureleri ya çıkarılmalı ya da daha fazla veri toplanana dek gözden geçirilmeli.

---

## 8. Koşula Göre Performans

`condition_analysis.csv` küçük örneklem üzerinde yön/koşul analizleri:

| Yön | N | Enhanced XGB MAE | RF MAE | XGBoost MAE |
|---|---:|---:|---:|---:|
| Halkapınar→Cengizhan | 6 | 0.4963 | 0.6360 | 0.6870 |
| Cengizhan→Halkapınar | 7 | 0.2605 | 0.5128 | 0.4710 |

- Cengizhan→Halkapınar yönünde Enhanced XGB **çok daha iyi** (MAE 0.26 vs 0.50).
- Halkapınar→Cengizhan yönünde fark daha az (0.50 vs 0.64).
- **Durak başlangıç bölgesinde (0-33%) MAE 0.3997** — orta/son bölgelere göre nasıl davrandığı tabloya alınmamış.

---

## 9. Literatürle Karşılaştırma

`paper_comparison.csv` — İstanbul LSTM çalışması ile:

| Metrik | Makale (Istanbul LSTM) | Bizim (Enhanced XGB) | Fark |
|---|---:|---:|---:|
| MAE (dk) | 2.97 | 0.3694 | **-87.6%** |
| MAPE (%) | 14.79 | 21.38 | +44.6% |
| R² | 0.9272 | 0.4885 | -47.3% |

### Yorumlar
- **MAE'de büyük üstünlük (~%88 daha düşük)** — ancak bu doğrudan kıyaslanabilir değil; bizim segment ortalama süresi 1.29 dk iken literatürdeki problem büyük ihtimalle uçtan uca yolculuk (çok daha uzun süreler).
- **MAPE daha kötü** — kısa segmentler (1 dk civarı) küçük mutlak hatayı bile büyük yüzde hataya çevirir.
- **R² daha düşük** — varyansın daha azını açıklıyoruz; yine kısa segment etkisi.

**Önemli:** Bu karşılaştırma makale içine konulurken metodolojik farklılıklar (segment vs trip, veri büyüklüğü, özellik seti) açıkça belirtilmeli; aksi halde yanıltıcı olur.

---

## 10. Özet ve Öneriler

### Güçlü Yönler
1. **Enhanced XGBoost** baseline'ları net biçimde geçiyor; en iyi tek model olarak ön plana çıkıyor.
2. Hybrid Stacking ek karmaşıklığa rağmen pratik bir kazanç sağlamıyor → **basit modeli tercih et**.
3. İstatistiksel testler bazı kıyaslamalarda anlamlılık gösteriyor.

### Zayıf Yönler ve Riskler
1. **Veri çok sınırlı (n_test=13, tek gün, tek saat dilimi).** Sonuçlar bu bağlamda dikkatli yorumlanmalı.
2. **Derin öğrenme modelleri başarısız** — şu anki sonuçlarla raporlanmamalı veya "veri yetersizliği" notu ile sunulmalı.
3. **Ablation, full-feature modelin en iyi olmadığını gösteriyor** → feature seçimi gerekli.
4. **MAPE değeri yüksek (%21.38)** — kısa segment ortalamalarında küçük hata bile yüzdeye yansıyor.
5. RF ve Historical Average'a karşı istatistiksel anlamlılık yok; bu makalede dürüstçe raporlanmalı.

### Eylem Listesi
- [ ] Daha fazla veri toplanması (en az birkaç hafta, peak/off-peak ve farklı hava koşulları dahil).
- [ ] Feature seçimi: `deviation_history` ve hava featurelerinin çıkarılması test edilmeli.
- [ ] DL modelleri için sequence boyu ve regularization ayarlanmalı; veri büyüdükçe yeniden değerlendirilmeli.
- [ ] Yön bazlı analizin tüm modellere genişletilmesi.
- [ ] Literatür karşılaştırmasında metodolojik farkların açık raporlanması.
- [ ] Final makale modeli olarak **Enhanced XGBoost** seçilmeli (basitlik + performans).
