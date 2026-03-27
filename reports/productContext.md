# Product Context

## Kullanici Personalari

### Persona 1: Bitirme Projesi Juri Uyesi
- **Kim:** GTU Bilgisayar Muhendisligi ogretim uyesi
- **Beklentisi:** Teknik derinlik, makale karsilastirmasi, ozgun katki kaniti, calisan kod
- **Degerlendirme Kriterleri:** Metodolojik tutarlilik, sonuclarin istatistiksel anlamliligi, raporlama kalitesi
- **Onem sirasi:** Sonuc metrikleri > Mimari > Kod kalitesi > Demo

### Persona 2: Toplu Tasima Planlayicisi (ESHOT)
- **Kim:** Izmir Buyuksehir Belediyesi ulasim departmani muhendisi
- **Beklentisi:** Gercek zamanli tahminler, durak bazli dogruluk, entegrasyon kolayligi
- **Kullanim senaryosu:** Durak bilgi panolarinda "otobus X dk sonra geliyor" gosterimi
- **Onem sirasi:** Dogruluk > Gercek zamanlilik > API entegrasyonu

### Persona 3: Yolcu
- **Kim:** Gunluk ESHOT kullanicisi (502 hatti)
- **Beklentisi:** Durakta "otobusum ne zaman gelecek?" sorusuna guvenilir cevap
- **Tolerans:** +-2 dakika hata kabul edilebilir, +-5 dakika hayal kirikligi
- **Onem sirasi:** Dogruluk > Hiz > Arayuz

---

## Feature Oncelikleri

### P0 — Kritik (Teslim icin zorunlu)
1. **Gercek zamanli veri toplama** — ESHOT GPS API'den surekli veri akisi ✅
2. **ML pipeline** — Veri → Feature → Model → Tahmin dongusu ✅
3. **Baseline karsilastirma** — En az 5 baseline model ile benchmark ✅
4. **Deep learning modeli** — LSTM/GRU ile temporal pattern yakalama ✅
5. **Makale karsilastirmasi** — Kaya & Kalay metrikleriyle dogrudan karsilastirma ✅

### P1 — Onemli (Iyi not icin gerekli)
6. **Hibrit ensemble** — Stacking meta-model ile optimum birlestirme ✅
7. **Ablation study** — GTFS feature katkisinin kaniti ✅
8. **Istatistiksel testler** — Paired t-test, Wilcoxon signed-rank ✅
9. **1+ haftalik gercek veri** — Anlamli sonuclar icin minimum veri ⬜

### P2 — Bonus (En iyi not icin)
10. **Demo web uygulamasi** — Flask tabanli canli tahmin dashboard ⬜
11. **SHAP analizi** — Feature importance goruntulemesi (kod hazir, shap kurulursa calisir) ✅
12. **Coklu rota genellestirme** — 502 disinda rotalara genisletme ⬜

---

## User Story'ler

### Veri Toplama
- ✅ Gelistirici olarak, `collector.py --test` ile API baglantisini dogrulayabilirim
- ✅ Gelistirici olarak, `collector.py --interval 30` ile surekli veri toplatabilirim
- ✅ Gelistirici olarak, `trip_extractor.py --stats` ile toplanan veriyi gorebilirim
- ✅ Gelistirici olarak, hava durumu API key'i olmasa bile mock veri ile calisabilirim

### Model Egitimi
- ✅ Arastirmaci olarak, notebook'lari sirayla calistirarak tum pipeline'i tekrarlayabilirim
- ✅ Arastirmaci olarak, baseline modellerle deep learning sonuclarini karsilastirabilirim
- ✅ Arastirmaci olarak, hibrit model ile en iyi performansi elde edebilirim
- ✅ Arastirmaci olarak, ablation study ile her feature'in katkisini olcebilirim

### Degerlendirme
- ✅ Juri uyesi olarak, makale metrikleriyle dogrudan karsilastirmayi gorebilirim
- ✅ Juri uyesi olarak, istatistiksel anlamlilik testlerini inceleyebilirim
- ⬜ Juri uyesi olarak, canli demo uzerinden tahmin dogrulugunu gozlemleyebilirim

---

## UX Prensipleri

1. **Tekrarlanabilirlik:** Tum pipeline notebook sirasiyla veya `nbconvert` ile command line'dan tekrarlanabilir
2. **Modulerlik:** Veri toplama, feature engineering, modelleme ve degerlendirme bagimsiz asamalar
3. **Hataya dayaniklilik:** API erisimi yoksa mock veri, shap yoksa XGBoost importance fallback
4. **Seffaflik:** Her asamanin ciktisi CSV/PNG olarak kaydedilir, sonraki asamaya girdi olur
