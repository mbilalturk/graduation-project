"""
Makale istatistikleri icin yardimcilar:
  - cohens_d_paired : eslestirilmis Cohen's d (per-segment |hata| farklari uzerinde)
  - cliffs_delta    : Cliff's delta (siralama tabanli, O(n log n))
  - day_block_bootstrap_ci : gun-bazli blok bootstrap CI
    (ayni gunun segmentleri korele oldugu icin satir-bazli bootstrap KULLANILMAZ)
"""
import numpy as np
import pandas as pd


def cohens_d_paired(a, b):
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    sd = d.std(ddof=1)
    if sd == 0:
        return 0.0
    return float(d.mean() / sd)


def cliffs_delta(a, b):
    a = np.asarray(a, dtype=float)
    b_sorted = np.sort(np.asarray(b, dtype=float))
    n1, n2 = len(a), len(b_sorted)
    lt = np.searchsorted(b_sorted, a, side="left")           # b < a_i sayisi -> a>b ciftleri
    gt = n2 - np.searchsorted(b_sorted, a, side="right")     # b > a_i sayisi -> a<b ciftleri
    return float((lt.sum() - gt.sum()) / (n1 * n2))


def day_block_bootstrap_ci(df, value_fn, date_col="date",
                           n_boot=1000, alpha=0.05, seed=42):
    rng = np.random.default_rng(seed)
    groups = {d: g for d, g in df.groupby(date_col)}
    days = np.array(list(groups.keys()))
    stats = np.empty(n_boot)
    for i in range(n_boot):
        sample_days = rng.choice(days, size=len(days), replace=True)
        sub = pd.concat([groups[d] for d in sample_days], ignore_index=True)
        stats[i] = value_fn(sub)
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)
