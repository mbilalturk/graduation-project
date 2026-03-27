# System Patterns

## Veritabani Semasi

### SQLite: `data_collector/collected_data/route_502_realtime.db`

```sql
-- Ana tablo: Her 30 saniyede polling ile alinan otobus GPS konumlari
CREATE TABLE bus_positions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL,           -- '2026-03-26 14:30:00'
    poll_id             TEXT NOT NULL,           -- '20260326_143000'
    otobus_id           INTEGER NOT NULL,        -- ESHOT otobus ID
    yon                 INTEGER NOT NULL,        -- 0: Halkapinar->Cengizhan, 1: Cengizhan->Halkapinar
    lat                 REAL NOT NULL,           -- Enlem (38.43-38.48 arasi)
    lon                 REAL NOT NULL,           -- Boylam (27.15-27.18 arasi)
    nearest_stop_id     INTEGER,                 -- En yakin durak ID
    nearest_stop_seq    INTEGER,                 -- En yakin durak sirasi
    distance_to_nearest_m REAL                   -- En yakin duraga mesafe (metre)
);
CREATE INDEX idx_bp_poll ON bus_positions(poll_id);
CREATE INDEX idx_bp_bus ON bus_positions(otobus_id, timestamp);

-- Kilit duraklara yaklasan otobusler (6 durak sorgulanir)
CREATE TABLE stop_arrivals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL,
    poll_id             TEXT NOT NULL,
    durak_id            INTEGER NOT NULL,        -- Durak ID
    otobus_id           INTEGER NOT NULL,
    hat_numarasi        INTEGER NOT NULL,        -- 502
    kalan_durak_sayisi  INTEGER NOT NULL,        -- Kalan durak (0 = duraga vardi)
    hattin_yonu         INTEGER NOT NULL,
    lat                 REAL NOT NULL,
    lon                 REAL NOT NULL
);
CREATE INDEX idx_sa_stop ON stop_arrivals(durak_id, timestamp);

-- Otobuslerin durak gecis olaylari (trip detection icin)
CREATE TABLE trip_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL,
    otobus_id           INTEGER NOT NULL,
    yon                 INTEGER NOT NULL,
    stop_id             INTEGER NOT NULL,
    stop_seq            INTEGER NOT NULL,
    stop_name           TEXT,
    event_type          TEXT NOT NULL,            -- 'arrival'
    lat                 REAL NOT NULL,
    lon                 REAL NOT NULL
);
CREATE INDEX idx_te_bus ON trip_events(otobus_id, timestamp);

-- Saatlik hava durumu kayitlari
CREATE TABLE weather_readings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp           TEXT NOT NULL,
    source              TEXT NOT NULL,            -- 'openweathermap' veya 'mock'
    temperature         REAL,                    -- Celsius
    humidity            REAL,                    -- %
    precipitation       REAL,                    -- mm/saat
    wind_speed          REAL,                    -- km/saat
    visibility          REAL,                    -- km
    conditions          TEXT,                    -- 'clear sky', 'rain' vb.
    weather_category    TEXT NOT NULL             -- 'clear', 'partly_cloudy', 'overcast', 'rainy'
);
CREATE INDEX idx_wr_ts ON weather_readings(timestamp);
```

---

## Tasarim Desenleri

### 1. Pipeline Pattern (Veri Akisi)

Sistem lineer bir pipeline olarak tasarlanmistir. Her asama bir oncekinin ciktisini girdi olarak alir:

```
collector.py → SQLite DB → trip_extractor.py → CSV
    → feature_engineering.ipynb → features CSV
        → baseline_models.ipynb → results CSV
        → deep_learning.ipynb → model .keras
        → hybrid_model.ipynb → ensemble model
            → evaluation.ipynb → final metrikler
```

**Neden:** Bitirme projesi baglami icin en basit ve debug edilebilir yaklasim. Her asamanin ciktisi bagimsiz olarak incelenebilir.

### 2. Polling + Event Detection

Collector, fixed-interval polling (varsayilan 30sn) yapar. Her pollingde:
1. Tum Route 502 otobus konumlarini ceker (GPS snapshot)
2. 6 kilit duraga yaklasan otobusleri sorgular
3. Her otobusun en yakin duragini hesaplar (Haversine mesafe)
4. Onceki konumla karsilastirip "durak gecisi" olayi uretir (`trip_events`)

**150m esigi:** Otobus duraga 150m'den yakinsa "durakta" kabul edilir.

### 3. Graceful Degradation (Hataya Dayaniklilik)

- **Hava durumu API key yok** → Deterministik mock veri (saat bazli, tekrarlanabilir)
- **SHAP kurulu degil** → XGBoost native feature importance
- **Az veri** → Selective Trend mekanizmasi (N<1000 icin GTFS + sapma trendi)
- **API baglanti hatasi** → Loglama + sonraki polling'e gecis (veri kaybi sadece o anlik)

### 4. Dual-Input Neural Network

LSTM/GRU modelleri iki ayri girdi kolu kullanir:
- **Sequence Branch:** Onceki N durağin [travel_time, scheduled_time, deviation, distance, progress] dizisi → LSTM 128 unit
- **Context Branch:** [hour, day_of_week, is_weekend, time_block, temperature, humidity, precipitation, is_rainy, weather] → Dense 32 unit

Iki kol birlestirilip Dense katmanlardan gecerek tek tahmin uretir.

### 5. Stacking Ensemble (Hibrit Model)

```
Selective Trend ──┐
Enhanced XGBoost ─┤──→ Ridge Meta-Model ──→ Final Tahmin
LSTM ─────────────┘
```

Her alt model bagimsiz tahmin uretir, Ridge regression optimum agirliklari ogrenir.

---

## Veri Akislari

### Gercek Zamanli Veri Toplama

```
ESHOT API (hatotobuskonumlari/502)
    → JSON parse (Turkce float: virgul→nokta)
    → En yakin durak hesapla (Haversine)
    → bus_positions tablosuna yaz
    → Trip event detection (onceki konum karsilastirma)
    → trip_events tablosuna yaz

ESHOT API (duragayaklasanotobusler/{durakId})
    → Sadece Route 502 filtrele
    → stop_arrivals tablosuna yaz

OpenWeatherMap API (saatlik)
    → weather_readings tablosuna yaz
```

### Feature Engineering Akisi

```
route_502_segments.csv (trip_extractor ciktisi)
    + GTFS stop_times.txt (planlanmis sureler)
    + weather_readings (SQLite'tan)
    ↓
Zamansal: hour, day_of_week, is_weekend, time_block
Mekansal: distance_m (Haversine), stop_progress (0-1)
GTFS: scheduled_travel_minutes, deviation_minutes
Hava: temperature, humidity, precipitation, wind_speed, visibility, weather_category, is_rainy
    ↓
route_502_features.csv (27 kolon)
```

---

## Guvenlik Mimarisi

### API Erisimi
- Izmir Teknoloji API: Anonim erisim, kimlik dogrulama gerektirmez
- OpenWeatherMap: API key cevre degiskeninden okunur (`OPENWEATHER_API_KEY`), kodda saklanmaz
- `.gitignore` ile veritabani ve hassas dosyalar repo'dan haric tutulur

### Veri Guvenligi
- Tum veri lokalde SQLite'ta saklanir, bulut servisi kullanilmaz
- Kisisel veri toplanmaz — sadece otobus ID ve GPS konumu (kamu verisi)
- API key sabit kodlanmaz, cevre degiskeni uzerinden alinir

### Hata Yonetimi
- API cagrilari try/except ile sarmalanir, loglama yapilir
- Timeout: 10 saniye (API cagrilari icin)
- Graceful shutdown: SIGINT/SIGTERM sinyalleri yakalanir, temiz kapatma yapilir
