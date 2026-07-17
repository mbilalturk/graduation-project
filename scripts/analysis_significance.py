"""
Effect size (Cohen's d, Cliff's delta) + gun-bazli bootstrap CI tablolari.
Girdi: improved_ml.py --save-preds ciktisi.

Segment-duzeyi paired testler ayni gunun segmentlerinin korelasyonunu yok sayar
(p iyimser cikar); bu yuzden gun-duzeyi kumelenmis test de raporlanir:
gun basina ortalama hata farki (~15 deger) uzerinde t-test / Wilcoxon.

Kullanim: PYTHONPATH=. python scripts/analysis_significance.py \
              --preds results/predictions/route_502_test_predictions.csv
"""
import os
import argparse
import numpy as np
import pandas as pd
from scipy import stats as sps

from scripts.stats_utils import cohens_d_paired, cliffs_delta, day_block_bootstrap_ci

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

MODEL_LABELS = {
    "pred_xgb_improved": "XGBoost (Improved)",
    "pred_rf_improved" : "RF (Improved)",
    "pred_rf_moe"      : "RF MoE",
    "pred_rf_base"     : "RF Baseline",
    "pred_histavg"     : "Historical Avg",
    "pred_naive"       : "Naive (GTFS)",
}
REFERENCE = "pred_xgb_improved"

ap = argparse.ArgumentParser()
ap.add_argument("--preds", required=True)
ap.add_argument("--n-boot", type=int, default=1000)
args = ap.parse_args()

df = pd.read_csv(args.preds)
pred_cols = [c for c in MODEL_LABELS if c in df.columns]
print(f"Yuklendi: {len(df)} satir, modeller: {pred_cols}")

# ── 1) Paired testler + effect size (referans: XGBoost Improved) ──────────────
err = {c: (df["y_true"] - df[c]).abs().values for c in pred_cols}
rows = []
for c in pred_cols:
    if c == REFERENCE:
        continue
    a, b = err[REFERENCE], err[c]     # a=referans hatalari, b=rakip hatalari
    t_p = sps.ttest_rel(a, b).pvalue
    w_p = sps.wilcoxon(a, b).pvalue if not np.allclose(a, b) else 1.0
    # gun-duzeyi kumelenmis test: gun basina ortalama hata farki (~15 deger)
    daily = pd.DataFrame({"date": df["date"].values, "d": a - b}).groupby("date")["d"].mean()
    t_p_daily = sps.ttest_1samp(daily, 0.0).pvalue
    w_p_daily = sps.wilcoxon(daily).pvalue if not np.allclose(daily, 0) else 1.0
    rows.append({
        "comparison"      : f"{MODEL_LABELS[REFERENCE]} vs {MODEL_LABELS[c]}",
        "n"               : len(a),
        "n_days"          : len(daily),
        "mae_a"           : round(a.mean(), 4),
        "mae_b"           : round(b.mean(), 4),
        "mae_diff"        : round(b.mean() - a.mean(), 4),
        "p_ttest"         : t_p,
        "p_wilcoxon"      : w_p,
        "p_ttest_daily"   : t_p_daily,
        "p_wilcoxon_daily": w_p_daily,
        "cohens_d"        : round(cohens_d_paired(a, b), 4),
        "cliffs_delta"    : round(cliffs_delta(a, b), 4),
    })
tests = pd.DataFrame(rows)
tests_path = os.path.join(PROJECT_ROOT, "results", "tables", "statistical_tests_v3.csv")
tests.to_csv(tests_path, index=False)
print(f"\n{tests.to_string(index=False)}\n-> {tests_path}")

# ── 2) Gun-bazli bootstrap CI (MAE + RMSE, model basina) ──────────────────────
ci_rows = []
for c in pred_cols:
    sub = df[["date", "y_true", c]].rename(columns={c: "pred"})
    mae  = (sub["y_true"] - sub["pred"]).abs().mean()
    rmse = np.sqrt(((sub["y_true"] - sub["pred"]) ** 2).mean())
    mae_lo, mae_hi = day_block_bootstrap_ci(
        sub, lambda s: (s["y_true"] - s["pred"]).abs().mean(), n_boot=args.n_boot)
    rmse_lo, rmse_hi = day_block_bootstrap_ci(
        sub, lambda s: float(np.sqrt(((s["y_true"] - s["pred"]) ** 2).mean())),
        n_boot=args.n_boot)
    ci_rows.append({"model": MODEL_LABELS[c],
                    "mae": round(mae, 4), "mae_ci_lo": round(mae_lo, 4),
                    "mae_ci_hi": round(mae_hi, 4),
                    "rmse": round(rmse, 4), "rmse_ci_lo": round(rmse_lo, 4),
                    "rmse_ci_hi": round(rmse_hi, 4)})
cis = pd.DataFrame(ci_rows).sort_values("mae")
ci_path = os.path.join(PROJECT_ROOT, "results", "tables", "metric_confidence_intervals.csv")
cis.to_csv(ci_path, index=False)
print(f"\n{cis.to_string(index=False)}\n-> {ci_path}")
