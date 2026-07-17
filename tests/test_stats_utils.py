import numpy as np
import pandas as pd
import pytest

from scripts.stats_utils import cohens_d_paired, cliffs_delta, day_block_bootstrap_ci


def test_cohens_d_paired_known_value():
    a = np.array([2.0, 3.0, 4.0, 5.0])
    b = np.array([1.0, 3.0, 3.0, 5.0])
    # d = a-b = [1,0,1,0]; mean=0.5, std(ddof=1)=0.5774 -> d ~= 0.866
    assert cohens_d_paired(a, b) == pytest.approx(0.866, abs=0.001)


def test_cohens_d_paired_zero_when_identical():
    a = np.array([1.0, 2.0, 3.0])
    assert cohens_d_paired(a, a) == 0.0


def test_cliffs_delta_extremes_and_zero():
    a = np.array([10.0, 11.0, 12.0])
    b = np.array([1.0, 2.0, 3.0])
    assert cliffs_delta(a, b) == 1.0      # a hep buyuk
    assert cliffs_delta(b, a) == -1.0     # a hep kucuk
    assert cliffs_delta(a, a) == 0.0      # ozdes


def test_cliffs_delta_mixed():
    a = np.array([1.0, 3.0])
    b = np.array([2.0, 2.0])
    # ciftler: (1,2)x2 a<b, (3,2)x2 a>b -> delta = (2-2)/4 = 0
    assert cliffs_delta(a, b) == 0.0


def test_day_block_bootstrap_ci_constant_metric():
    df = pd.DataFrame({
        "date": ["d1"] * 3 + ["d2"] * 3 + ["d3"] * 3,
        "err":  [1.0] * 9,
    })
    lo, hi = day_block_bootstrap_ci(df, lambda s: s["err"].mean(), n_boot=200)
    assert lo == pytest.approx(1.0)
    assert hi == pytest.approx(1.0)


def test_day_block_bootstrap_ci_contains_point_estimate():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "date": np.repeat([f"d{i}" for i in range(20)], 50),
        "err":  rng.normal(2.0, 0.5, 1000),
    })
    point = df["err"].mean()
    lo, hi = day_block_bootstrap_ci(df, lambda s: s["err"].mean(), n_boot=300)
    assert lo < point < hi
    assert (hi - lo) < 1.0  # makul genislik
