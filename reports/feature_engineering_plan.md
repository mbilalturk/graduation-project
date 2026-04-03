# Feature Engineering Planı

**Son Güncelleme:** 2026-04-03  
**Referans Makale:** Kaya & Kalay, IEEE Access 2025 — *Spatio-Temporal Forecasting of Bus Arrival Times*  
**Uygulanan Notebook:** `notebooks/feature_engineering_v2.ipynb`

---

## Hedef Değişken

Her segment için: **bir sonraki durağa geçen süre (dakika)** — `travel_time_min`

Her satır = bir otobüsün durak_i → durak_i+1 arasındaki tek geçişi.  
Bu yapı makaledeki ile birebir aynı: her geçiş bağımsız bir örnek.

---

## Kararlar (Kesinleşmiş)

| Karar | Uygulama |
|-------|---------|
| Zaman filtresi | 06:00–24:00 (makale ile aynı) |
| GTFS eşleşmeyenler | Çıkarılır (`inner join`) |
| `congestion_ratio` eksikse | 1.0 (serbest akış) ile doldurulur |
| `deviation_from_schedule` | Direkt feature değil — lag olarak kullanılır (target leakage önleme) |

---

## Veri Kaynakları

| Kaynak | Tablo / Dosya | Ne veriyor? |
|--------|--------------|-------------|
| ESHOT GPS API | `trip_events` | Otobüsün durak geçiş zamanları |
| OpenWeatherMap | `weather_readings` | Saatlik hava durumu |
| TomTom Traffic | `traffic_readings` | Segment bazlı trafik yoğunluğu |
| GTFS | `data/bus-eshot-gtfs/stop_times.txt` | Planlanmış hareket saatleri |

---

## Feature Tablosu

### GRUP 1 — Makaledeki Featurelar (Temel)

| Feature | Tip | Kaynak | Neden? |
|---------|-----|--------|--------|
| `prev_travel_time_min` | sürekli | trip_events (lag) | Makalenin `elapsed_time` feature'ı. Önceki durağa geçen gerçek süre. Otobüs o noktada hızlı/yavaş mı gittiğini gösterir. Trip başında 0.0. |
| `stop_progress` | sürekli | config.py koordinatları | Hattın yüzde kaçı geçildi (0.0=başlangıç, 1.0=son durak). `(max_seq - to_seq) / (max_seq - 1)` |
| `yon` | kategorik | trip_events | Gidiş (0) ve dönüş (1) farklı güzergah kullanıyor. |
| `day_type` | binary | timestamp | 0=hafta içi, 1=hafta sonu. Yolcu yoğunluğu ve trafik tamamen farklı. |
| `time_block` | kategorik | timestamp | 0=sabah pik (06-10), 1=gündüz (10-17), 2=akşam pik (17-20), 3=gece (20-24). |
| `temperature` | sürekli | weather_readings | Sıcak havalarda yolcu yavaş biner/iner. |
| `humidity` | sürekli | weather_readings | Dolaylı konfor etkisi. |
| `precipitation` | sürekli | weather_readings | Yağmurda sürüş ve yolcu hareketi yavaşlar — en kritik hava feature'ı. |
| `wind_speed` | sürekli | weather_readings | Açık güzergahlarda etkili. |
| `visibility` | sürekli | weather_readings | Sis/duman koşullarında sürüş yavaşlar. |
| `weather_cat_enc` | kategorik | weather_readings | clear=0, cloudy=1, rainy=2, snowy=3. |

### GRUP 2 — Bizim Eklediğimiz Featurelar (Özgün Katkı)

| Feature | Tip | Kaynak | Neden? |
|---------|-----|--------|--------|
| `scheduled_travel_min` | sürekli | GTFS stop_times.txt | ESHOT'un planladığı süre. Modelin "beklenen normal"i bilmesini sağlar. Makale bunu kullanmıyor — özgün katkı. |
| `prev_deviation` | sürekli | hesaplama (lag) | Önceki segmentte `gerçek - planlanmış`. Gecikmeler biriktiği için güçlü bir predictor. Lag olduğu için target leakage yok. |
| `congestion_ratio` | sürekli | traffic_readings (TomTom) | `current_speed / free_flow_speed`. 1.0=serbest, 0.3=ağır tıkanıklık. Makale trafik kullanmıyor — ciddi ek değer. |
| `distance_m` | sürekli | config.py (Haversine) | Duraklar arası fiziksel mesafe. Uzun segmentler kısa olanlara göre doğası gereği farklı davranır. |

### GRUP 3 — Encoding

| Feature | Dönüşüm | Neden? |
|---------|---------|--------|
| `hour` | `hour_sin`, `hour_cos` | Çembersel: 23 ile 0 arası fark 1 saat, lineer kodlamada 23 gibi görünür. |
| `day_of_week` | `dow_sin`, `dow_cos` | Çembersel: Pazar(6) ile Pazartesi(0) komşu. |
| `day_type` | 0/1 binary | Hafta içi=0, hafta sonu=1 |
| `time_block` | 0–3 label encode | morning_peak=0, off_peak=1, evening_peak=2, night=3 |
| `weather_cat_enc` | 0–3 label encode | clear=0, cloudy=1, rainy=2, snowy=3 |
| Tüm sürekli featurelar | MinMaxScaler [0,1] | Farklı ölçekler normalize edilir. Scaler sadece train setinden fit edilir (makale III.B.1). |

---

## Final Dataset Yapısı

### Model Girdisi (X) — 21 Feature

| # | Feature | Grup | Tip | Kaynak | Açıklama |
|---|---------|------|-----|--------|----------|
| 1 | `hour` | Zamansal | sürekli | timestamp | Varış saati (0–23), çembersel encoding için ham değer |
| 2 | `day_of_week` | Zamansal | sürekli | timestamp | 0=Pazartesi … 6=Pazar, çembersel encoding için ham değer |
| 3 | `day_type` | Zamansal | binary | timestamp | 0=hafta içi, 1=hafta sonu |
| 4 | `time_block` | Zamansal | kategorik | timestamp | 0=sabah pik (06-10), 1=gündüz (10-17), 2=akşam pik (17-20), 3=gece (20-24) |
| 5 | `hour_sin` | Zamansal | sürekli | timestamp | sin(2π × hour / 24) — çembersel encoding |
| 6 | `hour_cos` | Zamansal | sürekli | timestamp | cos(2π × hour / 24) — çembersel encoding |
| 7 | `dow_sin` | Zamansal | sürekli | timestamp | sin(2π × day_of_week / 7) — çembersel encoding |
| 8 | `dow_cos` | Zamansal | sürekli | timestamp | cos(2π × day_of_week / 7) — çembersel encoding |
| 9 | `stop_progress` | Mekansal | sürekli | config.py | Hattın yüzde kaçı geçildi: (max_seq − to_seq) / (max_seq − 1), 0.0=başlangıç 1.0=son durak |
| 10 | `distance_m` | Mekansal | sürekli | config.py (Haversine) | Duraklar arası fiziksel mesafe (metre) |
| 11 | `prev_travel_time_min` | Lag | sürekli | trip_events | Önceki segmentin gerçek süresi — makalenin `elapsed_time` feature'ı. Trip başında 0.0. |
| 12 | `prev_deviation` | Lag | sürekli | hesaplama | Önceki segmentte gerçek − planlanmış süre (dk). Gecikmeler biriktiği için güçlü predictor. |
| 13 | `scheduled_travel_min` | GTFS | sürekli | stop_times.txt | ESHOT'un bu segment için planladığı süre. Makale bunu kullanmıyor — özgün katkı. |
| 14 | `temperature` | Hava | sürekli | weather_readings | Hava sıcaklığı (°C) |
| 15 | `humidity` | Hava | sürekli | weather_readings | Nem oranı (%) |
| 16 | `precipitation` | Hava | sürekli | weather_readings | Yağış miktarı (mm) — en kritik hava feature'ı |
| 17 | `wind_speed` | Hava | sürekli | weather_readings | Rüzgar hızı (km/h) |
| 18 | `visibility` | Hava | sürekli | weather_readings | Görüş mesafesi (km) |
| 19 | `weather_cat_enc` | Hava | kategorik | weather_readings | clear=0, cloudy=1, rainy=2, snowy=3 |
| 20 | `congestion_ratio` | Trafik | sürekli | traffic_readings (TomTom) | current_speed / free_flow_speed. 1.0=serbest akış, 0.3=ağır tıkanıklık. Makale bunu kullanmıyor — özgün katkı. |
| 21 | `yon` | Güzergah | binary | trip_events | 0=Halkapınar→Cengizhan, 1=Cengizhan→Halkapınar |

### Hedef (y)

| Feature | Açıklama |
|---------|----------|
| `travel_time_min` | Durak_i → Durak_i+1 gerçek geçiş süresi (dakika) |

**Makale:** 6 feature → **Bizim:** 21 feature (trafik + GTFS + lag + çembersel encoding)

---

## v1 → v2 Değişiklikleri

| # | Sorun | v1 | v2 |
|---|-------|----|----|
| 1 | Target leakage | `deviation_from_schedule` direkt feature | `prev_deviation` lag feature olarak kullanılır |
| 2 | Eksik feature | `elapsed_time_min` hiç yoktu | `prev_travel_time_min` eklendi |
| 3 | GPS jitter | `seq == prev_seq` → yanlış trip bölmesi | `continue` ile event atlanır |
| 4 | Traffic merge | O(n²) nested groupby loop | `merge_asof` + `by` parametresi, O(n log n) |
| 5 | Yavaş hesaplama | `iterrows()` + `haversine_m` | Koordinat tablosu merge + vektörize Haversine |
| 6 | stop_progress | Son durağa varışta 0.97 | `(max_seq - to_seq) / (max_seq - 1)` → 1.0 |
| 7 | Veri kaynağı | CSV (trip_extractor çıktısı) | Doğrudan `eshot_buses.db` |
