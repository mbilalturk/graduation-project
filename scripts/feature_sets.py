"""
Additive ablation feature setleri (SCI: hoca madde 1).
  c0: baglamsiz taban (temporal + spatial)
  c1: + GTFS tarife       (scheduled_travel_min)
  c2: + sapma/lag baglami (prev/cumul/rolling deviation + is_trip_start)
  c3: + tarihsel          (stop_hist_median/ratio, prev_speed_mpm)
  c4: + dwell             (dwell_time_sec, prev_dwell_time_sec — v4 verisi)
LSTM icin c0/c1 kosulamaz: sequence girdisi dogasi geregi lag icerir
(izgarada N/A birakilir, makalede aciklanir).
"""
FEATURE_SETS = {}
FEATURE_SETS["c0"] = ["hour", "day_of_week",
                      "from_stop_seq", "to_stop_seq", "distance_m", "stop_progress"]
FEATURE_SETS["c1"] = FEATURE_SETS["c0"] + ["scheduled_travel_min"]
FEATURE_SETS["c2"] = FEATURE_SETS["c1"] + ["prev_travel_time_min", "prev_deviation",
                                           "cumul_deviation", "rolling_3_deviation",
                                           "is_trip_start"]
FEATURE_SETS["c3"] = FEATURE_SETS["c2"] + ["stop_hist_median", "stop_hist_ratio",
                                           "prev_speed_mpm"]
FEATURE_SETS["c4"] = FEATURE_SETS["c3"] + ["dwell_time_sec", "prev_dwell_time_sec"]

LSTM_ALLOWED = ("c2", "c3", "c4", "full")
