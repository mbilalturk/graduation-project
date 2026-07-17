"""
Model x feature-set izgarasi (RQ merkez deneyi).

Iki tablo uretir:
1) ablation_grid_route_502.csv — satir=model, sutun=config, hucre=MAE.
   XGB/RF: tam segment test seti MAE'si. LSTM: kapsanan alt kume MAE'si
   (sequence uretilebilen satirlar; c0/c1 = NA, mimari gereği — sequence
   girdisi dogasi geregi lag icerir).
2) ablation_grid_covered_route_502.csv — ADIL model-ekseni kiyasi:
   her config icin XGB ve LSTM, LSTM'in kapsayabildigi AYNI satirlarda
   karsilastirilir (same-test-set ilkesinin alt-kume versiyonu).

Kullanim: PYTHONPATH=. python scripts/build_ablation_grid.py
"""
import os
import numpy as np
import pandas as pd

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
TAB = os.path.join(PROJECT_ROOT, "results", "tables")
PRED = os.path.join(PROJECT_ROOT, "results", "predictions")

CONFIGS = ["c0", "c1", "c2", "c3", "c4"]

# ── 1) Ana izgara ─────────────────────────────────────────────────────────────
abl = pd.read_csv(os.path.join(TAB, "ablation_additive_route_502.csv"))
grid = {}
for model_key, label in [("XGBoost", "XGBoost"), ("RF", "Random Forest")]:
    sub = abl[abl["model"].str.startswith(model_key)]
    grid[label] = {r["config"]: r["MAE (dk)"] for _, r in sub.iterrows()}

lstm = pd.read_csv(os.path.join(TAB, "ablation_additive_lstm_route_502.csv"))
grid["LSTM (covered subset)"] = {
    **{c: np.nan for c in ["c0", "c1"]},          # mimari geregi N/A
    **{r["config"]: r["MAE_covered"] for _, r in lstm.iterrows()},
}

gdf = pd.DataFrame(grid).T[CONFIGS]
gdf.index.name = "model"
gpath = os.path.join(TAB, "ablation_grid_route_502.csv")
gdf.to_csv(gpath)
print("MODEL x FEATURE-SET IZGARASI (MAE, dk):")
print(gdf.to_string())
print(f"-> {gpath}\n")

# ── 2) Kapsanan alt kumede adil XGB vs LSTM kiyasi ────────────────────────────
rows = []
for cfg in ["c2", "c3", "c4"]:
    lpath = os.path.join(PRED, f"route_502_test_predictions_lstm_fs-{cfg}.csv")
    xpath = os.path.join(PRED, f"route_502_test_predictions_fs-{cfg}.csv")
    if not (os.path.exists(lpath) and os.path.exists(xpath)):
        print(f"  {cfg}: predictions eksik, atlandi")
        continue
    l = pd.read_csv(lpath)
    x = pd.read_csv(xpath)
    assert len(l) == len(x), (cfg, len(l), len(x))
    # ayni siralamayla uretildiler (ayni kronolojik %80/20 split); yine de dogrula
    assert (l["arrival_timestamp"].values == x["arrival_timestamp"].values).all(), cfg
    cov = l["pred_lstm"].notna().values
    err_l = (l.loc[cov, "y_true"] - l.loc[cov, "pred_lstm"]).abs().mean()
    err_x = (x.loc[cov, "y_true"] - x.loc[cov, "pred_xgb_improved"]).abs().mean()
    rows.append({"config": cfg, "n_covered": int(cov.sum()),
                 "coverage_pct": round(100 * cov.mean(), 1),
                 "mae_xgb_covered": round(err_x, 4),
                 "mae_lstm_covered": round(err_l, 4),
                 "diff_lstm_minus_xgb": round(err_l - err_x, 4)})
cdf = pd.DataFrame(rows)
cpath = os.path.join(TAB, "ablation_grid_covered_route_502.csv")
cdf.to_csv(cpath, index=False)
print("KAPSANAN ALT KUMEDE MODEL EKSENI (ayni satirlar, XGB vs LSTM):")
print(cdf.to_string(index=False))
print(f"-> {cpath}")

# RQ ozeti: feature ekseni vs model ekseni
xgb_row = gdf.loc["XGBoost"]
feat_axis = float(xgb_row["c0"] - xgb_row["c4"])
if len(cdf):
    model_axis = float(cdf["diff_lstm_minus_xgb"].abs().max())
    print(f"\nRQ OZETI: feature ekseni (XGB c0->c4) MAE'yi {feat_axis:.3f} dk oynatiyor; "
          f"model ekseni (XGB vs LSTM, ayni satirlar) en fazla {model_axis:.3f} dk. "
          f"Oran ~{feat_axis/max(model_axis, 1e-9):.0f}x.")
