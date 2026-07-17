# SCI Makale Yol Haritası — Hoca Değerlendirmesi Analizi ve Deney Planı

**Tarih:** 2026-07-17
**Girdiler:** [hoca_değerlendirme.md](hoca_değerlendirme.md), [bus-arrival-prediction-izmir-report.pdf](bus-arrival-prediction-izmir-report.pdf) (hocanın değerlendirdiği final rapor), `results/tables/`, `scripts/`, `collected_data/route_502_features_v2.csv`
**Amaç:** Hocanın SCI makalesi önündeki engel olarak gördüğü sorunların (1) gerçekten var olup olmadığını repo üzerinde doğrulamak, (2) her biri için somut deney/çözüm tasarımı vermek, (3) hocaya sorulması gereken açık soruları listelemek. Bu doküman tek başına tüm durumu göstermek için yazılmıştır.

---

## 0. İlerleme TODO — SCI Makaleye Giden Yol

> Her aşama bittiğinde kutusu işaretlenir. Detaylar: Faz A → §9, hoca soruları → §7.

**Faz A — Yerel analiz katmanı** ✅ 10/10 (2026-07-17 tamamlandı)
- [x] İstatistik altyapısı: effect size + gün-bazlı blok bootstrap CI (`stats_utils.py`, TDD)
- [x] `improved_ml.py`: feature-set / save-preds / CV-split / core-only + leakage-safe historical (headline birebir korundu)
- [x] Additive ablation C0–C4 × {XGB, RF} × 3 hat
- [x] LSTM ablation C2–C4 + **model × feature-set ızgarası** (RQ merkez deneyi: ~9× oran)
- [x] Rolling-origin 5-fold CV (XGB 0.4406 ± 0.0277)
- [x] Significance tabloları: segment + gün-düzeyi p, Cohen's d, Cliff's δ, CI
- [x] Hata kırılımları: saat, zaman bloğu, hafta sonu, segment uzunluğu, yön + figürler
- [x] Yağmur analizi fold-içi kontrollü (+0.051 ± 0.050 dk; naif farkın çoğu confound)
- [x] Trip-progress (cold-start) figürü — full + C0 + C1 katmanlı
- [x] Trip-level aggregation (10 durak: 2.45 dk; göreli hata %35→%16.9)

**Faz B — Hoca ile hizalama** ⬜ 0/3
- [ ] Bu doküman + §9 sonuçları hocaya iletilir
- [ ] §7 sorularına cevap alınır (özellikle: RQ kurgusu onayı, hedef dergi, yağmur kapsamı, LSTM çerçevelemesi)
- [ ] Veri toplayıcının yeniden başlatılması kararı (collector 13 Haziran'dan beri kapalı)

**Faz C — Tamamlayıcı deneyler** ⬜ 0/2 *(hoca cevabına göre kapsam netleşir)*
- [ ] LSTM rolling-origin CV (5 gecelik koşum; opsiyonel robustluk eki)
- [ ] (Veri toplama yeniden başlarsa) genişleyen veriyle koşumların tazelenmesi

**Faz D — Literatür ve konumlandırma** ⬜ 0/3
- [ ] Literatür taraması (SCI için 30–60 referans; şu an 5)
- [ ] Kaya & Kalay künyesinin tamamlanması (yazar adları, cilt, sayfa)
- [ ] Related work + novelty konumlandırması ("bağlam > model" tezinin literatürdeki yeri)

**Faz E — Makale yazımı** ⬜ 0/4
- [ ] IMRaD taslak yapısı + bölüm planı (ayrı plan dokümanı)
- [ ] Figür/tablo son seçimi ve İngilizce cilalama
- [ ] Metodoloji notlarının işlenmesi (§9.4: gün=bağımsızlık birimi, LSTM N/A hücreleri, yağmur fold-içi, trip-level iyimserlik notu)
- [ ] İç inceleme + hocaya taslak teslimi

**Faz F — Başvuru** ⬜ 0/2
- [ ] Hedef dergi formatına geçirme (dergi kararı Faz B'de)
- [ ] Cover letter + submission

---

## 1. Yönetici Özeti

Hocanın 7 tespitinin **5'i tamamen doğru** (ablation, trip-progress grafiği, effect size, güven aralığı, detaylı hata analizi), **1'i kısmen doğru** (cross-validation: time-based split zaten var ama hiç CV yok), **1'inde de hocanın bilmediği bir iyi haber var** (yağmur verisi artık mevcut — 11 yağışlı gün).

Kritik bulgu: Final raporun ana iddiası (*"GTFS schedule-derived ve dwell-time feature'ları en bilgilendirici girdiler arasında"* — Abstract ve Contributions §1.4) **raporda hiçbir deneyle desteklenmiyor.** Hoca "ama bunun kanıtı yok" derken tam isabet.

İyi haber: İstenen her şey **mevcut veri ve mevcut pipeline üzerinde analiz katmanı işi.** Yeni model, yeni mimari, zorunlu yeni veri toplama gerekmiyor. Toplam efor kabaca 2–3 haftalık odaklı çalışma.

---

## 2. Projenin Güncel Durumu (doğrulanmış rakamlar)

| Konu | Durum |
|---|---|
| Veri aralığı | **2026-04-02 → 2026-06-13, 73 gün** (`route_502_features_v2.csv` üzerinde doğrulandı; collector 13 Haziran'da durdu) |
| Hat 502 | 81.575 segment (train 65.260 / test 16.315) |
| Hat 268 / 565 | 115.803 / 114.572 segment (temiz, hat-parametrik feature'larla) |
| En iyi modeller | XGBoost Improved MAE **0.4327** ≈ LSTM 0.4345 (p=0.38, fark yok) > RF 0.4378 (p≤0.0055) |
| Baseline'lar | Historical Avg 0.645, Naive GTFS 0.734 (R²=−0.05) |
| Split | `improved_ml.py:87` — tarihe göre sıralama + %80/20 → **fiilen kronolojik split** (ilk ~58 gün train / son ~15 gün test) |
| Cold-start | İlk %33 durakta MAE 0.541 vs orta bölge 0.345 (**~1.5×**); 5 fill stratejisi A/B'sinde hiçbiri kapatamadı → içsel zorluk |
| Yağmur | **11 yağışlı gün**, 502 setinde 2.068 yağışlı segment, mevcut test setinde 324 (rainy MAE 0.595 vs clear 0.444) |
| İstatistiksel testler | Paired t-test + Wilcoxon var; **effect size ve CI yok** |
| Ablation | Eski (leakage dönemi, 3 hat karışık veri) ablation geçersiz; `results/tables/`'da güncel ablation dosyası **yok** |
| Tekrarlanabilirlik | seed=42, tüm sonuçlar reprodüsibl; kod CLI-parametrik (`--route`, `--coldstart`, `--target`, HP argümanları) |

### Elde duran ve makale tezini destekleyen bulgular

- XGBoost ≈ LSTM (istatistiksel eşdeğerlik) → "model seçimi belirleyici değil"
- Feature seti 29→16'ya inince MAE iyileşti → "daha çok feature ≠ daha iyi"
- 3 negatif A/B (GPS interpolasyon, deviation hedefi, HP tuning) → "30 sn polling'in dayattığı ölçüm tabanı (quantization floor)"
- Cold-start hiçbir doldurma stratejisiyle kapanmıyor → "bağlam feature'ları boşken hata katlanıyor"
- Yöntem 3 hatta tutarlı (MAE 0.30–0.43) → genelleme

---

## 3. Önerilen Research Question Kurgusu

Hocanın önerisi: *"Otobüs seyahat süresi tahminindeki temel problem model seçimi değil, yolculuk bağlamının doğru oluşturulmasıdır."*

Bu kurgu eldeki bulgularla zaten örtüşüyor ve aşağıdaki üç katkı bunun altına doğal olarak diziliyor:

1. **Feature engineering framework** (scheduled travel time + cumulative deviation + dwell üçlüsü) → kanıtı **additive ablation** (§4.1)
2. **Cold-start'ın sistematik analizi** → bağlam tezinin doğal deneyi: bağlam feature'ları boşken hata 1.5× katlanıyor; schedule feature'ı bunu kısmen telafi ediyor (§4.2)
3. **Cause-effect analysis** → her kırılım analizinin (saat, segment uzunluğu, yağmur, yön) nedeniyle birlikte raporlanması (§4.6–4.7)

Destekleyici argümanlar: XGB≈LSTM eşdeğerliği ve negatif A/B bulguları ("daha sofistike model değil, daha iyi bağlam").

> **Hocaya doğrulatılacak** — bkz. §7 Soru 1.

---

## 4. Hocanın Tespitleri: Madde Madde Analiz ve Çözüm Tasarımı

### 4.1. Feature Contribution Analysis (ablation) — hocanın 1. maddesi

**Hocanın tespiti:** "GTFS, Deviation, Dwell önemli diyoruz ama bunun kanıtı yok. Önce base sonuç alıp sonra tek tek eklenip kıyaslanmalı."

**Mevcut durum:** Final raporda ablation yok. Tek ilgili deney Step 2 feature selection A/B'si (29→16) — o da "gereksiz feature atınca hata artmıyor"u gösteriyor, "GTFS/deviation/dwell değer katıyor"u değil. Eski `ablation_study.csv` leakage dönemi + 3 hat karışık veriyle üretilmişti, geçersiz ve zaten silinmiş.

**Hüküm: GERÇEK EKSİK — en yüksek öncelik.** Makalenin ana iddiası şu an kanıtsız.

**Çözüm tasarımı — additive (kümülatif) ablation:**

Rapor Table 3.1'deki feature gruplarına dayalı konfigürasyon merdiveni:

| Konfig | İçerik | Beklenen anlatı |
|---|---|---|
| C0 (base) | Temporal (hour, dow, weekend) + Spatial (distance, stop_progress) | "Bağlamsız" taban |
| C1 | C0 + **Schedule (GTFS)**: scheduled_travel_min | GTFS'in tek başına katkısı |
| C2 | C1 + **Deviation/Lag**: prev_travel_time, prev_deviation, kümülatif/rolling sapma | Gerçek zamanlı bağlamın katkısı |
| C3 | C2 + **Dwell**: dwell_time, prev_dwell | Durak dinamiğinin katkısı |
| C4 (full) | C3 + Historical (durak medyanı, önceki hız) + trip-start bayrağı | Tam model (=mevcut 16 feature) |

**Tasarım kararları:**
- **Model × feature ızgarası:** Her konfig hem XGBoost hem LSTM ile koşulur. Böylece tek tabloda "feature ekseni MAE'yi X kadar oynatıyor, model ekseni Y≪X kadar" gösterilir → RQ'nun merkez deneyi. (RF opsiyonel üçüncü satır.)
- **3 hat:** Ana sonuç 502'de; 268 ve 565'te tekrar → "framework hat-bağımsız" genelleme kanıtı.
- Ardışık konfigler arası fark, paired test + effect size (§4.3) ile raporlanır.

**İmplementasyon:** `improved_ml.py` ve `improved_lstm.py`'a `--feature-set {c0,c1,c2,c3,c4}` argümanı (feature listeleri tek yerde tanımlı). Çıktı: `results/tables/ablation_additive_route_<RID>.csv`. LSTM için context feature alt kümeleri aynı mantıkla kısıtlanır; sequence girdisinde scheduled/deviation kanalları konfige göre maskelenir.

**Efor:** ~2-3 gün (kod yarım gün; 5 konfig × 2 model × 3 hat koşumları; LSTM koşumları gecelik).

---

### 4.2. Error by Trip Progress — hocanın 2. maddesi

**Hocanın tespiti:** "Cold-start analizi güzel ama sadece sayı görmek istemeyiz; grafikleştirmek ve öne çıkarmak gerekir."

**Mevcut durum:** Final raporda Table 5.3'te 3 kaba bin (0-33%: 0.541 / 33-66%: 0.345 / 66-100%: 0.365) + bir paragraf. Grafik yok, ince taneli analiz yok.

**Hüküm: GERÇEK EKSİK.** Projenin en ilginç bulgusu görselleştirilmemiş.

**Çözüm tasarımı:**
- **Ana figür:** X = `segments_into_trip` (1, 2, 3, … ~15+, üst uç birleştirilmiş), Y = MAE, model başına eğri, gün-bazlı bootstrap CI bandı (§4.4 altyapısını kullanır). Cold-start bölgesi gölgelendirilir.
- **İkinci katman (ablation bağlantısı):** Aynı grafiğe C1 (schedule'lı) vs C0 (schedule'sız) modellerinin eğrileri bindirilir → "İlk duraklarda hata neden yüksek?" (lag feature'lar boş) ve "Schedule neden azaltıyor?" (GTFS önceliği bağlam boşluğunu dolduruyor) sorularının **tek figürde** cevabı. Hocanın istediği cause-effect anlatısının görsel merkezi.
- Yan panel: her pozisyondaki n ve ortalama gerçek süre (hatanın süre artışından değil bağlam eksikliğinden geldiğini ayrıştırmak için normalize MAE/scheduled eğrisi de eklenebilir).

**Çıktı:** `results/figures/error_by_trip_progress.png` + `results/tables/error_by_trip_progress.csv`
**Efor:** ~1 gün (ablation modelleri hazırsa yarım gün).

---

### 4.3. Effect Size — hocanın 3. maddesi

**Hocanın tespiti:** "Sadece p-value yeterli olmaz; Cohen's d veya Cliff's Delta eklenmeli."

**Mevcut durum:** `statistical_tests.csv` sadece MAE farkı, t-stat, p (t-test), p (Wilcoxon) içeriyor. n=16.315'te neredeyse her fark "anlamlı" çıkıyor — hocanın işaret ettiği sorun tam bu.

**Hüküm: GERÇEK EKSİK — en ucuz düzeltme.**

**Çözüm tasarımı:**
- Her model çifti için per-segment mutlak hata dizileri üzerinden:
  - **Paired Cohen's d:** d = mean(|e_A|−|e_B|) / std(|e_A|−|e_B|)
  - **Cliff's delta:** δ = P(|e_A|>|e_B|) − P(|e_A|<|e_B|); yorum eşikleri: |δ|<0.147 ihmal edilebilir, <0.33 küçük, <0.474 orta, ≥0.474 büyük
- `statistical_tests.csv`'e iki kolon eklenir; makale tablosunda p + effect size birlikte.
- **Beklenen (ve işimize yarayan) sonuç:** XGB vs LSTM'de d≈0 / δ≈0 → "model seçimi pratik fark yaratmıyor" tezi p=0.38'den çok daha güçlü anlatılır; model vs baseline'da büyük etki → bağlam feature'larının katkısı nicelenir.

**İmplementasyon:** evaluation pipeline'ında predictions zaten satır-hizalı mevcut; saf post-processing.
**Efor:** ~2-3 saat.

---

### 4.4. Confidence Interval — hocanın 4. maddesi

**Hocanın tespiti:** "MAE/RMSE için tek sayı yerine güven aralığı eklenebilir."

**Mevcut durum:** Tüm metrikler tek sayı.

**Hüküm: GERÇEK EKSİK.**

**Çözüm tasarımı:**
- **Gün-bazlı blok bootstrap** (B=1000): test setindeki *günler* iadeli örneklenir, her örneklemde MAE/RMSE yeniden hesaplanır → yüzdelik %95 CI. Satır-bazlı bootstrap **kullanılmaz** çünkü aynı günün segmentleri korele (hava, trafik, olaylar) — hakem sorarsa savunulabilir olan gün-bloğu.
- Kapsam: ana model tablosu (Table 5.1 muadili) + tüm alt-grup analizleri (özellikle yağmur n=324 — CI genişliği dürüstçe gösterilir).
- Aynı altyapı §4.2 ve §4.6-4.7 figürlerinin CI bantlarını da üretir.

**İmplementasyon:** Tek yardımcı fonksiyon (`scripts/` altına `bootstrap_ci.py` ya da evaluation notebook'una hücre); kayıtlı per-segment tahminler üzerinde çalışır.
**Efor:** ~yarım gün.

---

### 4.5. Cross-Validation ve Time-based Split — hocanın 5. maddesi

**Hocanın tespiti:** "80/20 split var; en az 5-fold CV görmek ister hakemler. Ayrıca 80/20 yerine time-based split (ilk 50 gün train / son 15 gün test) anlamlı."

**Mevcut durum — kısmen yanlış alarm:**
- Split **zaten time-based**: `improved_ml.py:87` veriyi tarihe göre sıralayıp %80/20 bölüyor; 73 günde bu ≈ ilk 58 gün train / son 15 gün test. Final rapor da bunu yazıyor (§3.4.2 "split chronologically") ama görünürde yeterince vurgulanmamış — hoca random split sanıyor. **Yapılacak ilk iş: bunu hocaya netleştirmek** (bkz. §7 Soru 2).
- **Gerçek eksik: hiçbir CV yok.** Tek split, tek test penceresi; sonuçların son 15 güne özgü olmadığının kanıtı yok.

**Hüküm: YARISI YANLIŞ ALARM (split), YARISI GERÇEK (CV yok).**

**Çözüm tasarımı — rolling-origin (expanding window) CV:**

Düz shuffle 5-fold burada **yanlış olur** (gelecek bilgisi train'e sızar; lag/historical feature'lar temporal leakage üretir). Zaman serisi problemine uygun olan:

| Fold | Train | Test |
|---|---|---|
| 1 | Gün 1–28 | Gün 29–37 |
| 2 | Gün 1–37 | Gün 38–46 |
| 3 | Gün 1–46 | Gün 47–55 |
| 4 | Gün 1–55 | Gün 56–64 |
| 5 | Gün 1–64 | Gün 65–73 |

- Rapor formatı: model başına MAE ortalama ± std (5 fold) + fold bazlı tablo. "Hakemler 5-fold ister" isteğini metodolojik olarak daha güçlü bir kurguyla karşılar.
- Historical feature'lar (durak medyanı vb.) her fold'da yalnızca o fold'un train penceresinden hesaplanır (mevcut leakage-safe kurulum korunur).
- LSTM: fold başına tek koşum, sabit seed (compute: 5 koşum, gecelik). XGB/RF hızlı.
- **Yan fayda:** 11 yağışlı günün 7'si fold test pencerelerinin kapsadığı 29. gün sonrası dönemde → yağmur analizi (§4.7) fold'lar birleştirilerek çok daha geniş yağışlı test örneklemine kavuşur.
- Ana başlık (headline) sonuçları yine tek kronolojik split'te kalabilir; CV robustluk bölümü olur. İstenirse headline split hocanın önerdiği "ilk 50 / son 15 gün" olarak yeniden tanımlanır (mevcut 58/15'ten farkı kozmetik).

**İmplementasyon:** `improved_ml.py` / `improved_lstm.py`'a `--train-end-day` / `--test-days` (veya `--fold k`) argümanı + koşumları döngüleyen küçük bir driver script. Çıktı: `results/tables/cv_rolling_origin_route_<RID>.csv`.
**Efor:** ~2 gün (kod 1 gün + koşumlar).

---

### 4.6. Error by Time of Day — hocanın 8. maddesi

**Hocanın tespiti:** "time_of_day'e göre yapılmış ama zenginleştirilip sabah/öğlen/akşam performansları da görülmeli."

**Mevcut durum:** 4 blok var (morning_peak 0.464 / off_peak 0.439 / evening_peak 0.388 / night 0.366) — ama sadece tablo. Figure 5.2 hata değil *ortalama seyahat süresi* gösteriyor; hata-analizi figürü değil.

**Hüküm: KISMEN VAR — zenginleştirme ve görselleştirme eksik.**

**Çözüm tasarımı:**
- **Saat-saat MAE eğrisi (06–22):** X = saat, Y = MAE, CI bantlı, ikinci eksende n. Sabah pikinin (07–09) tepe yaptığı, akşamın daha kolay olduğu görünür kılınır.
- Hocanın istediği gruplama: sabah (06–10) / öğlen (10–16) / akşam (16–20) / gece (20–22) — CI + effect size ile.
- **Cause-effect notu:** sabah piki neden daha zor (okul+iş çakışması, kalkış yoğunluğu, değişkenlik ↑) — hata varyansı ve gerçek süre varyansı yan yana gösterilerek desteklenir.

**Çıktı:** `results/figures/error_by_hour.png` + tablo. **Efor:** ~yarım gün.

---

### 4.7. Detaylı Hata Analizi — hocanın 9. maddesi

**Hocanın tespiti:** "Hangi örneklerde hata oluştuğunun detaylı analizi: kısa/uzun segment, pik saat, gece/gündüz, yağmur, hafta sonu."

**Mevcut durum ve hüküm — alt madde bazında:**

| Kırılım | Durum | Yapılacak |
|---|---|---|
| Kısa/uzun segment | **YOK** | `scheduled_travel_min` (ve `distance_m`) çeyreklerine göre MAE + **göreli hata** (MAE/scheduled). Beklenen bulgu: 30 sn kuantalama tabanı kısa segmentlerde oransal olarak daha ağır → "MAPE neden %41" sorusunun cevabı; ölçüm-tabanı anlatısıyla birleşir. |
| Pik saat | Kısmen var | §4.6 içinde CI + effect size ile derinleştirilir |
| Gece/gündüz | Kısmen var (night bloğu) | §4.6 saatlik eğri kapsar |
| **Yağmur** | Rapor "n küçük" deyip limitation'a atmış; **ama sinyal var** | rainy MAE 0.595 vs clear 0.444 (+%34). Gün-bazlı CI + Cliff's delta ile **dürüst bir bulgu olarak** raporlanır. CV fold'ları birleştirilerek yağışlı test örneklemi büyütülür (§4.5 yan faydası). Yağışlı/kuru *gün* karşılaştırması (11 vs 62 gün) ikincil kontrol olarak eklenir. |
| Hafta sonu | **YOK** | `day_of_week`'ten hafta içi/hafta sonu MAE + CI + effect size. Cause-effect: hafta sonu trafik varyansı düşük → beklenen daha düşük MAE; tersi çıkarsa da raporlanır. |

**Çıktı:** `results/tables/error_slices_route_502.csv` + 2-3 figür. **Efor:** ~1 gün (CI altyapısı hazırsa).

---

## 5. Bizim Eklediğimiz Öneriler (hoca istemedi ama makaleyi güçlendirir)

1. **Trip-level aggregation deneyi.** Kaya & Kalay kıyası şu an "elma-armut" (segment vs uçtan uca trip). Segment tahminlerini trip boyunca toplayıp **uçtan uca varış MAE'si** üretirsek kıyas adil hale gelir ve muhtemelen güçlü bir sayı çıkar (segment hataları kısmen bağımsızsa toplamda kancellenir). Makale için hem yeni sonuç hem savunma kalkanı. *(Efor: ~1-2 gün.)*
2. **Ablation'ın 3 hatta tekrarı** (§4.1'de gömülü) — "framework genelleniyor" iddiasını feature katkısı düzeyine indirir; SCI için ayırt edici olur.
3. **Ölçüm tabanı (quantization floor) bulgusunu makalenin satış noktalarından biri yapmak.** Üç negatif A/B (GPS interpolasyon %8 kapsama, deviation hedefi, HP tuning) tesadüfen değil sistematik olarak aynı tabana çarpıyor. "Public 30 sn polling ile ulaşılabilir doğruluğun sınırı" başlı başına aktarılabilir bir bulgu; cold-start ve kısa-segment analizleriyle tutarlı bir "veri kalitesi > model karmaşıklığı" anlatısı kuruyor.
4. **Veri toplamayı yeniden başlatmak.** Collector 13 Haziran'da durdu. SCI süreci aylar sürer; collector bugün yeniden açılırsa (a) veri bedavaya büyür, (b) sonbahar yağmurları yağmur analizini kökten güçlendirir, (c) "3 ay" yerine "6+ ay" veri SCI için daha etkileyici. Maliyeti: sunucunun açık kalması. *(Karar hocayla — §7 Soru 3.)*

---

## 6. Öncelik, Efor ve Önerilen Sıra

Bağımlılıklar: CI altyapısı (§4.4) diğer tüm analizlerin bantlarını ürettiği için önce gelmeli; ablation (§4.1) trip-progress figürünün ikinci katmanını beslediği için ondan önce.

| Sıra | İş | Hoca maddesi | Efor | Bağımlılık |
|---|---|---|---|---|
| 1 | Effect size (Cohen's d + Cliff's δ) | 3 | 2-3 saat | — |
| 2 | Gün-bazlı bootstrap CI altyapısı | 4 | 0.5 gün | — |
| 3 | Saatlik hata eğrisi + zaman dilimi zenginleştirme | 8 | 0.5 gün | 2 |
| 4 | Hata kırılımları (segment uzunluğu, hafta sonu, yağmur v1) | 9 | 1 gün | 2 |
| 5 | Additive ablation (5 konfig × 2 model × 3 hat) | 1 | 2-3 gün | — (koşumlar gecelik) |
| 6 | Trip-progress figürü (ablation katmanlı) | 2 | 0.5-1 gün | 2, 5 |
| 7 | Rolling-origin CV (5 fold, 3 model) | 5 | 2 gün | — (koşumlar gecelik) |
| 8 | Yağmur analizi v2 (CV fold'ları birleşik örneklem) | 9 | 0.5 gün | 7 |
| 9 | (Öneri) Trip-level aggregation | — | 1-2 gün | — |

Toplam: ~2-3 hafta odaklı çalışma (koşumlar gecelik paralelde).

---

## 7. Hocaya Sorulacak Sorular

1. **RQ kurgusu onayı:** "Temel problem model seçimi değil bağlam kurulumu" tezini merkez alıyoruz; ablation'ı bu yüzden feature-seti × model ızgarası olarak kurguladık (feature ekseninin model ekseninden çok daha belirleyici olduğunu tek tabloda göstermek için). Bu kurgu sizin kafanızdaki kurguyla örtüşüyor mu?
2. **Split netleştirmesi:** Mevcut 80/20 split aslında random değil, kronolojik (tarihe göre sıralı; fiilen ilk ~58 gün train / son 15 gün test — raporda §3.4.2'de geçiyor ama vurgusuz kalmış). Önerdiğiniz "ilk 50 / son 15 gün" ile pratikte aynı. CV için shuffle 5-fold yerine **rolling-origin (genişleyen pencere) 5-fold** öneriyoruz çünkü shuffle bu problemde temporal leakage üretir — uygun mudur, yoksa hakem beklentisi için klasik 5-fold da ayrıca raporlansın mı?
3. **Veri toplama:** Collector 13 Haziran'dan beri kapalı. Makale takvimi düşünülünce yeniden başlatalım mı? (Bedava veri büyümesi + sonbahar yağmurlarıyla yağmur analizinin güçlenmesi; buna karşılık sonuçların yeniden koşulması gerekir.)
4. **Yağmur analizi kapsamı:** Şu an test setinde 324 yağışlı segment var; CI'lı ve effect size'lı dürüst raporlama ile makaleye koymayı öneriyoruz (CV fold birleşimi örneklemi büyütüyor). Yeterli görür müsünüz, yoksa yağışlı veri büyüyene kadar "ileri çalışma" mı kalsın?
5. **Hedef dergi:** IEEE Access mi (referans makale orada), Transportation Research Part C / IET ITS gibi alan dergisi mi? Bu; ablation derinliği, literatür taraması genişliği ve trip-level deneyin gerekliliğini etkiler.
6. **Trip-level aggregation:** Kaya & Kalay ile adil kıyas için segment tahminlerini uçtan uca varış süresine toplayan bir deney eklemeyi öneriyoruz (§5.1). Kapsama alalım mı?
7. **LSTM'in konumu:** XGB≈LSTM bulgusu makalede "DL gerekmiyor" mesajına dönüşecek. Bu çerçeveleme sizce dergi/hakem açısından risk mi, güç mü? (Biz güç olduğunu düşünüyoruz: negatif sonuç + ölçüm tabanı anlatısıyla tutarlı.)

---

## 8. Riskler ve Açık Konular

- **LSTM ablation/CV compute:** 5 konfig + 5 fold LSTM koşumu ≈ 10 gecelik koşum; takvime yayılmalı. XGB/RF önemsiz.
- **Yağmur örnekleminin küçüklüğü:** CV birleşimiyle büyüse de gün sayısı 11'de kalıyor; iddialar "hata artışı gözlemleniyor (geniş CI)" tonunda kalmalı, "yağmur şunu kanıtlar" tonuna kaçmamalı.
- **Ablation'da LSTM sequence girişi:** C0/C1 konfiglerinde sequence kanallarından scheduled/deviation'ın çıkarılması mimari küçük değişiklik gerektirir; maskeleme yaklaşımı en temizi.
- **Eski rapor/tablolarla tutarlılık:** Yeni analizler üretilirken `results/tables/` içinde eski-yeni karışmaması için dosya adlarında sürüm/tarih disiplini (örn. `_v3` veya tarih eki) uygulanmalı.
- **Referans makale kimliği:** Bibliyografyada Kaya & Kalay girdisi eksik bilgiyle duruyor ("complete author initials, volume and page numbers before final submission" notu kalmış) — makale öncesi tamamlanmalı.

---

## 9. Uygulama Durumu (2026-07-17 — yerel analiz katmanı tamamlandı)

Plan: `docs/superpowers/plans/2026-07-17-sci-local-analysis.md` (12 task'ın tamamı koşuldu; tüm sonuçlar seed=42 ile reprodüsibl). Headline davranış korundu: argümansız `improved_ml.py --route 502` koşumu commit'li `improved_ml_results.csv` ile **bayt-aynı** sonuç veriyor (XGBoost MAE 0.4327).

### 9.1. Üretilen analizler ve dosyalar

| Hoca maddesi | Çıktı | Dosyalar |
|---|---|---|
| 1 — Ablation | Additive C0–C4 × {XGB, RF} × 3 hat + LSTM C2–C4 + **model×feature ızgarası** | `results/tables/ablation_additive_route_{502,268,565}.csv`, `ablation_additive_lstm_route_502.csv`, `ablation_grid_route_502.csv`, `ablation_grid_covered_route_502.csv` |
| 2 — Trip-progress | MAE vs `segments_into_trip` figürü (full + C0 + C1, CI bantlı, cold-start gölgeli) | `results/figures/error_by_trip_progress.png`, `results/tables/error_by_trip_progress.csv` |
| 3 — Effect size | Cohen's d + Cliff's δ, tüm model çiftleri | `results/tables/statistical_tests_v3.csv` |
| 4 — CI | Gün-bazlı blok bootstrap (B=1000) MAE/RMSE %95 CI | `results/tables/metric_confidence_intervals.csv` |
| 5 — CV | Rolling-origin 5-fold (28/37/46/55/64 gün train, 9'ar gün test) | `results/tables/cv_rolling_origin_route_502.csv` + `_summary` |
| 8 — Saat bazlı | Saatlik MAE eğrisi + zaman blokları, CI'li | `results/figures/error_by_hour*.png`, `results/tables/error_slices_route_502*.csv` |
| 9 — Kırılımlar | Segment uzunluğu, hafta sonu, yağmur (fold-içi kontrollü), yön | aynı slices tabloları + `rain_within_fold_route_502_pooled.csv`, `error_by_segment_length*.png`, `error_by_weather*.png` |
| (öneri) Trip-level | Kümülatif varış MAE'si vs horizon | `results/tables/trip_level_mae_route_502.csv`, `results/figures/trip_level_error_vs_horizon.png` |

Altyapı: `scripts/stats_utils.py` (TDD, 6 test), `scripts/feature_sets.py` (tek doğruluk kaynağı), `scripts/run_ablation.py`, `scripts/run_cv.py`, `scripts/analysis_{significance,error_slices,trip_progress,trip_level}.py`, `scripts/build_ablation_grid.py`; `improved_ml.py`'a `--feature-set/--save-preds/--train-end-day/--test-days/--core-only` + leakage-safe historical yeniden hesaplama; `improved_lstm.py`'a `--feature-set/--save-preds` + segment-level hizalama.

### 9.2. Headline sayılar

**Model × feature-set ızgarası (RQ merkez deneyi, 502, MAE dk):**

| | C0 | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|
| XGBoost | 0.5604 | 0.5605 | 0.4924 | 0.4930 | 0.4310 |
| Random Forest | 0.5670 | 0.5670 | 0.4913 | 0.4905 | 0.4388 |
| LSTM (kapsanan alt küme) | N/A* | N/A* | 0.3828 | 0.3660 | 0.3532 |

\* Mimari gereği: sequence girdisi doğası gereği lag içerir; makalede tek cümleyle açıklanacak.

- **RQ kanıtı:** Feature ekseni (XGB C0→C4) MAE'yi **0.129 dk** oynatıyor; model ekseni (aynı satırlarda XGB vs LSTM, `ablation_grid_covered`) en fazla **0.015 dk** — **~9×** fark. C4'te XGB 0.3533 vs LSTM 0.3532 (fiilen özdeş).
- **Ablation deseni 3 hatta tutarlı:** C1≈C0, C2'de büyük düşüş, C4'te (dwell) belirgin düşüş (502: 0.492→0.431; 268: 0.383→0.371; 565: 0.309→0.304).
- **CV:** XGBoost 5-fold MAE **0.4406 ± 0.0277** (RF 0.4450 ± 0.0275) — headline 0.4327 bandın içinde; sonuçlar tek test penceresine özgü değil.
- **Effect size:** XGB vs RF: p_t=0.0008 ("anlamlı") ama d=−0.026, δ=−0.011 (**ihmal edilebilir**) → "istatistiksel anlamlılık ≠ pratik fark" anlatısının kanıtı. XGB vs Naive: δ=−0.34 (orta-büyük). Gün-düzeyi p'ler (n_days=23) segment-düzeyinden büyük, sıralama aynı.
- **CI:** XGB MAE 0.4327 [0.4105, 0.4548]; ilk üç modelin CI'ları örtüşüyor (eşdeğerlik görsel olarak da savunulabilir).
- **Yağmur (fold-içi kontrollü):** Naif tek-split farkı +0.151 dk iken fold-içi rainy−clear farkı **+0.051 ± 0.050 dk** (4 fold'un 1'inde negatif) → tek-split farkının büyük kısmı erken-fold/az-train confound'u. Makalede "küçük, geniş CI'lı gözlem" tonunda verilecek.
- **Trip-level:** 10 durak ilerisi kümülatif varış MAE **2.45 dk** (naive 4.82; kansellasyonsuz üst sınır 5.45). Göreli hata horizon'la düşüyor: %35 (1 durak) → **%16.9** (10 durak) → MAPE %41 eleştirisine trip ölçeğinde cevap. Kaya & Kalay'ın 2.97 dk'sıyla aynı ölçekte kıyaslanabilir sayı.

### 9.3. Beklentiyle çelişen dürüst bulgular (makalede cause-effect malzemesi)

1. **Statik GTFS tek başına katkısız (C1≈C0, üç hatta da).** Ağaç modelleri segment kimliğini (`from/to_stop_seq`) zaten ezberliyor; tarife bilgisi segment kimliğinin fonksiyonu olduğu için marjinal bilgi eklemiyor. GTFS'in gerçek değeri **deviation feature'ları üzerinden** (tarifeye göre sapma = gerçek zamanlı bağlam) geliyor — C2 sıçraması bunun kanıtı. "GTFS önemli" iddiası makalede bu şekilde inceltilmeli.
2. **Trip-progress figüründe C1 eğrisi C0'la üst üste** — "schedule cold-start'ı telafi eder" hipotezi doğrulanmadı. Cold-start'ta hatayı düşüren şey full modelin dwell + diğer bağlam feature'ları (pos 0'da C0/C1 1.01 vs full 0.55).
3. **Yağmur etkisinin büyük kısmı confound çıktı** (bkz. 9.2) — fold-içi kontrol olmasaydı makaleye abartılı bir bulgu girecekti.
4. **Trip gözlemi çok parçalı:** test setindeki 3.324 trip'in 2.354'ü tek segmentlik (GPS-durak eşleşmesi seyrek). Trip-level analiz "baştan eksiksiz gözlenen" triplerle yapıldı (0 trip atıldı ama k≥3 horizon'a yalnız ~950 trip ulaşıyor) ve bu alt küme genelden daha uzun/yavaş segmentler içeriyor (seçim etkisi tabloda `linear_ref` ile dürüstçe normalize edildi).
5. **LSTM kapsaması %42.6:** window=7 nedeniyle LSTM, segment test setinin ancak yarısından azına tahmin üretebiliyor; scheduled-fallback'li tam-test MAE (0.65) model kıyası için anlamsız — bu yüzden model ekseni kıyası **kapsanan ortak alt kümede** yapıldı (`ablation_grid_covered_route_502.csv`).

### 9.4. Makale yazımına taşınacak notlar

- Izgarada LSTM×C0/C1 hücreleri "N/A — sequence input inherently contains lag information" dipnotuyla verilecek.
- İstatistik metodolojisi tek ilkeyle anlatılacak: **gün = bağımsızlık birimi** (gün-bazlı blok bootstrap CI + gün-düzeyi kümelenmiş testler; segment-düzeyi p'ler ek olarak raporlanır, iyimserlik uyarısıyla).
- Yağmur bulgusu yalnız fold-içi kontrollü haliyle sunulacak.
- Trip-level sayı sunulurken "one-step-ahead tahminlerin toplamı = çoklu-adım tahminin iyimser kestirimi" notu düşülecek (aynı koşul naive için de geçerli, kıyas iç tutarlı).
- LSTM eğitim scriptindeki trip gruplaması `(bus_id, yon, trip_start_time)` — date içermiyor; ~%1,4 trip çakışması var (bilinen küçük kusur, tüm konfigleri eşit etkilediği için ızgara kıyası geçerli; ileride düzeltilebilir).

### 9.5. Kalan işler

- **LSTM rolling-origin CV** (5 gecelik koşum) — opsiyonel robustluk eki; `improved_lstm.py`'a `--train-end-day` eklenerek koşulur.
- **Literatür taraması + bibliyografya** (30–60 referans; Kaya & Kalay girdisinin tamamlanması) — teslim öncesine ertelendi, ayrı planlanacak.
- **Hoca soruları (§7)** — özellikle RQ kurgusu onayı ve veri toplamanın yeniden başlatılması kararı.

---

## 10. Sonraki Adımlar

1. Bu doküman hocaya iletilir; §7'deki sorulara cevap alınır (özellikle 1, 2, 3).
2. Cevaplar beklenirken sıra 1–4 (effect size, CI, saatlik eğri, kırılımlar) başlatılabilir — hangi RQ kurgusu seçilirse seçilsin hepsi gerekli.
3. RQ onayı gelince ablation (sıra 5) ve CV (sıra 7) koşulur; figürler üretilir.
4. Tüm tablolar/figürler hazır olunca makale taslağına geçilir (ayrı plan).
