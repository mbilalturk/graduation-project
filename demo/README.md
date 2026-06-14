# Demo — Bus Arrival Time Prediction

Materials for the graduation-project demo video. **Bilingual (English + Turkish).**

## Contents
| File | Description |
|------|-------------|
| **`index.html`** | Demo dashboard — **English** (default). Double-click → opens in browser. |
| **`index_tr.html`** | Demo dashboard — **Turkish**. |
| **`script_en.md`** | Speech script — **English** (~3.5–4 min, with screen cues). |
| **`konusma_metni.md`** | Speech script — **Turkish**. |
| **`build_demo.py`** | Generator that rebuilds both dashboards from the real result CSVs. |

The dashboards are **self-contained**: no server and no internet required (all real
data is embedded). Just double-click the HTML file. Full screen (F11) recommended for recording.

## Rebuild after new results
```bash
python demo/build_demo.py        # writes index.html (EN) + index_tr.html (TR)
```
Data sources: `results/tables/full_comparison_table.csv`, `condition_analysis.csv`,
`multi_route_comparison.csv`, `data_summary.csv`, `paper_comparison.csv`, and
`collected_data/route_502_features_v4.csv` (for the interactive prediction).

## Dashboard sections
1. Dataset summary (81,575 segments, 73 days)
2. Model comparison (XGBoost ≈ LSTM > RF)
3. **Live prediction** (pick a segment + time of day → estimate)
4. Condition-based analysis (direction / time / weather / stop zone)
5. Generalization (3 routes)
6. Reference comparison + methodological findings

All numbers come from the reproducible (seed=42) outputs under `results/`.
