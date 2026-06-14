# Demo — Otobüs Varış Süresi Tahmini

Bitirme projesi demo videosu için hazırlanan materyaller.

## İçerik
- **`index.html`** — Self-contained demo dashboard'u. **Çift tıkla, tarayıcıda açılır.**
  Sunucu veya internet gerektirmez (tüm gerçek veri dosyaya gömülüdür).
- **`konusma_metni.md`** — Video için Türkçe konuşma metni (sahne/ekran ipuçlarıyla, ~3.5–4 dk).
- **`build_demo.py`** — Dashboard'u gerçek sonuç CSV'lerinden yeniden üreten script.

## Kullanım

### Demo'yu aç
`demo/index.html` dosyasına çift tıkla (veya tarayıcıya sürükle). Video için tam ekran (F11) önerilir.

### Yeni sonuçlarla güncelle
Modelleri yeniden çalıştırdıysan dashboard'u tazele:
```bash
python demo/build_demo.py
```
Script şu dosyalardan veri çeker:
`results/tables/full_comparison_table.csv`, `condition_analysis.csv`,
`multi_route_comparison.csv`, `data_summary.csv`, `paper_comparison.csv`,
ve `collected_data/route_502_features_v4.csv` (interaktif tahmin için).

## Dashboard bölümleri
1. Veri kümesi özeti (81.575 segment, 73 gün)
2. Model karşılaştırması (XGBoost ≈ LSTM > RF)
3. **Canlı tahmin denemesi** (segment + zaman dilimi seç → tahmin)
4. Koşul bazlı analiz (yön / zaman / hava / durak bölgesi)
5. Genelleme (3 hat)
6. Makale kıyası + metodolojik bulgular

Tüm sayılar `results/` altındaki tekrarlanabilir (seed=42) çıktılardan gelir.
