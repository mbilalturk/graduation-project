"""Route Data Collector - Configuration"""

import csv
import os

# --- API endpoints ---
BASE_URL = "https://openapi.izmir.bel.tr/api/iztek"
ENDPOINT_BUS_POSITIONS      = f"{BASE_URL}/hatotobuskonumlari/{{hat_id}}"
ENDPOINT_BUSES_AT_STOP      = f"{BASE_URL}/duragayaklasanotobusler/{{durak_id}}"
ENDPOINT_ROUTE_BUSES_AT_STOP = f"{BASE_URL}/hattinyaklasanotobusleri/{{hat_id}}/{{durak_id}}"

# --- Backward-compat: Route 502 sabitleri (notebook'lar hala kullanabilir) ---
ROUTE_ID   = 502
ROUTE_NAME = "CENGİZHAN - HALKAPINAR METRO"

# Route 502 stops - Direction 0 (Cengizhan -> Halkapinar Metro)
STOPS_DIR0 = [
    {"stop_id": 31082, "seq": 1,  "name": "Cengizhan Son Durak",        "lat": 38.4772, "lon": 27.1690},
    {"stop_id": 31140, "seq": 2,  "name": "Borsa Okulu Eski Sondurak",  "lat": 38.4768, "lon": 27.1699},
    {"stop_id": 31138, "seq": 3,  "name": "Yeşil Ulu Cami",             "lat": 38.4754, "lon": 27.1669},
    {"stop_id": 31080, "seq": 4,  "name": "Yasemin",                    "lat": 38.4767, "lon": 27.1638},
    {"stop_id": 31078, "seq": 5,  "name": "Sağlık Ocağı",               "lat": 38.4766, "lon": 27.1596},
    {"stop_id": 31070, "seq": 6,  "name": "Cengizhan 75.Yıl Lisesi",    "lat": 38.4753, "lon": 27.1579},
    {"stop_id": 31068, "seq": 7,  "name": "75.Yıl Parkı",               "lat": 38.4740, "lon": 27.1567},
    {"stop_id": 31072, "seq": 8,  "name": "Birkent 2",                  "lat": 38.4729, "lon": 27.1571},
    {"stop_id": 31066, "seq": 9,  "name": "Birkent",                    "lat": 38.4729, "lon": 27.1588},
    {"stop_id": 31064, "seq": 10, "name": "Durmuş Yaşar İlköğretim",    "lat": 38.4725, "lon": 27.1608},
    {"stop_id": 31062, "seq": 11, "name": "Alpaslan",                   "lat": 38.4713, "lon": 27.1636},
    {"stop_id": 31048, "seq": 12, "name": "PTT Santral",                "lat": 38.4699, "lon": 27.1652},
    {"stop_id": 31046, "seq": 13, "name": "Alparslan Mah. Muhtarlık",   "lat": 38.4697, "lon": 27.1671},
    {"stop_id": 30996, "seq": 14, "name": "Taş Ocağı",                  "lat": 38.4684, "lon": 27.1683},
    {"stop_id": 30994, "seq": 15, "name": "Mavi Köşe",                  "lat": 38.4680, "lon": 27.1665},
    {"stop_id": 30992, "seq": 16, "name": "Adil Akçamlı",               "lat": 38.4670, "lon": 27.1655},
    {"stop_id": 30998, "seq": 17, "name": "Köprü",                      "lat": 38.4658, "lon": 27.1635},
    {"stop_id": 20055, "seq": 18, "name": "Bayraklı Çamlık",            "lat": 38.4671, "lon": 27.1611},
    {"stop_id": 20134, "seq": 19, "name": "Bayraklı Üst Geçit",         "lat": 38.4641, "lon": 27.1625},
    {"stop_id": 30956, "seq": 20, "name": "Piyale",                     "lat": 38.4613, "lon": 27.1696},
    {"stop_id": 30290, "seq": 21, "name": "Smyrna",                     "lat": 38.4604, "lon": 27.1732},
    {"stop_id": 30286, "seq": 22, "name": "Manas",                      "lat": 38.4579, "lon": 27.1751},
    {"stop_id": 30284, "seq": 23, "name": "Bayraklı Depo",              "lat": 38.4559, "lon": 27.1764},
    {"stop_id": 30282, "seq": 24, "name": "Halide Edip Adıvar",         "lat": 38.4522, "lon": 27.1784},
    {"stop_id": 30280, "seq": 25, "name": "Adliye",                     "lat": 38.4500, "lon": 27.1796},
    {"stop_id": 30140, "seq": 26, "name": "Üçüncü Sanayi",              "lat": 38.4458, "lon": 27.1810},
    {"stop_id": 30138, "seq": 27, "name": "Bölge İdare Mahkemesi",      "lat": 38.4432, "lon": 27.1800},
    {"stop_id": 11892, "seq": 28, "name": "Çınarlı Mes.Tek.AL",         "lat": 38.4408, "lon": 27.1753},
    {"stop_id": 31547, "seq": 29, "name": "Çınarlı Diş Hastanesi",      "lat": 38.4397, "lon": 27.1734},
    {"stop_id": 31545, "seq": 30, "name": "Halkapınar Spor Salonu",     "lat": 38.4353, "lon": 27.1730},
    {"stop_id": 12874, "seq": 31, "name": "Halkapınar Tramvay",         "lat": 38.4335, "lon": 27.1704},
    {"stop_id": 10462, "seq": 32, "name": "Halkapınar Metro",           "lat": 38.4331, "lon": 27.1693},
]

# Route 502 stops - Direction 1 (Halkapinar Metro -> Cengizhan)
STOPS_DIR1 = [
    {"stop_id": 10462, "seq": 1,  "name": "Halkapınar Metro",           "lat": 38.4331, "lon": 27.1693},
    {"stop_id": 31543, "seq": 2,  "name": "Çamdibi Sağlık Ocağı",       "lat": 38.4353, "lon": 27.1730},
    {"stop_id": 30139, "seq": 3,  "name": "Mersinli",                   "lat": 38.4397, "lon": 27.1734},
    {"stop_id": 30141, "seq": 4,  "name": "Stadyum İstasyon",           "lat": 38.4408, "lon": 27.1753},
    {"stop_id": 30138, "seq": 5,  "name": "Bölge İdare Mahkemesi",      "lat": 38.4432, "lon": 27.1800},
    {"stop_id": 30140, "seq": 6,  "name": "Üçüncü Sanayi",              "lat": 38.4458, "lon": 27.1810},
    {"stop_id": 30280, "seq": 7,  "name": "Adliye",                     "lat": 38.4500, "lon": 27.1796},
    {"stop_id": 30282, "seq": 8,  "name": "Halide Edip Adıvar",         "lat": 38.4522, "lon": 27.1784},
    {"stop_id": 30284, "seq": 9,  "name": "Bayraklı Depo",              "lat": 38.4559, "lon": 27.1764},
    {"stop_id": 30286, "seq": 10, "name": "Manas",                      "lat": 38.4579, "lon": 27.1751},
    {"stop_id": 30290, "seq": 11, "name": "Smyrna",                     "lat": 38.4604, "lon": 27.1732},
    {"stop_id": 30958, "seq": 12, "name": "Matbaa",                     "lat": 38.4613, "lon": 27.1696},
    {"stop_id": 30960, "seq": 13, "name": "Yunus Keskin Parkı",         "lat": 38.4641, "lon": 27.1625},
    {"stop_id": 30992, "seq": 14, "name": "Adil Akçamlı",               "lat": 38.4670, "lon": 27.1655},
    {"stop_id": 30994, "seq": 15, "name": "Mavi Köşe",                  "lat": 38.4680, "lon": 27.1665},
    {"stop_id": 30996, "seq": 16, "name": "Taş Ocağı",                  "lat": 38.4684, "lon": 27.1683},
    {"stop_id": 31046, "seq": 17, "name": "Alparslan Mah. Muhtarlık",   "lat": 38.4697, "lon": 27.1671},
    {"stop_id": 31048, "seq": 18, "name": "PTT Santral",                "lat": 38.4699, "lon": 27.1652},
    {"stop_id": 31062, "seq": 19, "name": "Alpaslan",                   "lat": 38.4713, "lon": 27.1636},
    {"stop_id": 31064, "seq": 20, "name": "Durmuş Yaşar İlköğretim",    "lat": 38.4725, "lon": 27.1608},
    {"stop_id": 31066, "seq": 21, "name": "Birkent",                    "lat": 38.4729, "lon": 27.1588},
    {"stop_id": 31068, "seq": 22, "name": "75.Yıl Parkı",               "lat": 38.4740, "lon": 27.1567},
    {"stop_id": 31070, "seq": 23, "name": "Cengizhan 75.Yıl Lisesi",    "lat": 38.4753, "lon": 27.1579},
    {"stop_id": 31078, "seq": 24, "name": "Sağlık Ocağı",               "lat": 38.4766, "lon": 27.1596},
    {"stop_id": 31080, "seq": 25, "name": "Yasemin",                    "lat": 38.4767, "lon": 27.1638},
    {"stop_id": 31138, "seq": 26, "name": "Yeşil Ulu Cami",             "lat": 38.4754, "lon": 27.1669},
    {"stop_id": 31140, "seq": 27, "name": "Borsa Okulu Eski Sondurak",  "lat": 38.4768, "lon": 27.1699},
    {"stop_id": 31082, "seq": 28, "name": "Cengizhan Son Durak",        "lat": 38.4772, "lon": 27.1690},
]

ALL_STOP_IDS = list({s["stop_id"] for s in STOPS_DIR0 + STOPS_DIR1})

# --- Collection settings ---
POLL_INTERVAL_SECONDS = 30
DATA_DIR = "collected_data"


# ---------------------------------------------------------------------------
# Top-30 Hat: GTFS'ten dinamik olarak yuklenen cok-hat konfigurasyonu
# Sira: gunluk sefer sayisina gore azalan (GTFS trips.txt analizi)
# ---------------------------------------------------------------------------
ACTIVE_ROUTE_IDS = [268, 565, 502]

ACTIVE_ROUTE_IDS_SET = set(ACTIVE_ROUTE_IDS)

# GTFS statik veri klasoru (config.py'nin bir ust dizininde)
GTFS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "bus-eshot-gtfs")
)


def _load_routes_from_gtfs():
    """
    GTFS dosyalarindan top-30 hatin durak listelerini yukle.

    Doner:
        {
            route_id (int): {
                "dir0": [{"stop_id", "seq", "name", "lat", "lon"}, ...],
                "dir1": [...]
            },
            ...
        }

    Her hat icin dir0 ve dir1 icin birer temsilci trip secilir;
    o trip'in durak sirasi kullanilir.
    """
    stops_file      = os.path.join(GTFS_DIR, "stops.txt")
    trips_file      = os.path.join(GTFS_DIR, "trips.txt")
    stop_times_file = os.path.join(GTFS_DIR, "stop_times.txt")

    # 1. stops.txt: stop_id -> {name, lat, lon}
    stops_info = {}
    with open(stops_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stops_info[row["stop_id"]] = {
                "name": row["stop_name"],
                "lat":  float(row["stop_lat"]),
                "lon":  float(row["stop_lon"]),
            }

    # 2. trips.txt: her (route_id, direction_id) icin ilk trip_id'yi sec
    target_routes = {str(r) for r in ACTIVE_ROUTE_IDS}
    rep_trips = {}   # (route_id_str, dir_str) -> trip_id
    with open(trips_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["route_id"] not in target_routes:
                continue
            key = (row["route_id"], row["direction_id"])
            if key not in rep_trips:
                rep_trips[key] = row["trip_id"]

    needed_trips = set(rep_trips.values())

    # 3. stop_times.txt: secili trip'lerin durak siralarini yukle
    #    (87MB dosyayi bir kez tarar, sadece ihtiyac duyulan trip_id'leri alir)
    trip_stops = {tid: [] for tid in needed_trips}
    with open(stop_times_file, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["trip_id"] not in trip_stops:
                continue
            trip_stops[row["trip_id"]].append(
                (int(row["stop_sequence"]), row["stop_id"])
            )
    for tid in trip_stops:
        trip_stops[tid].sort(key=lambda x: x[0])

    # 4. ROUTES sozlugunu olustur
    routes = {}
    for route_id_int in ACTIVE_ROUTE_IDS:
        rid = str(route_id_int)
        entry = {"dir0": [], "dir1": []}
        for dir_key in ("0", "1"):
            tid = rep_trips.get((rid, dir_key))
            if tid is None:
                continue
            dir_label = f"dir{dir_key}"
            for seq, sid in trip_stops.get(tid, []):
                if sid not in stops_info:
                    continue
                s = stops_info[sid]
                entry[dir_label].append({
                    "stop_id": int(sid),
                    "seq":     seq,
                    "name":    s["name"],
                    "lat":     s["lat"],
                    "lon":     s["lon"],
                })
        routes[route_id_int] = entry
    return routes


# GTFS yuklenemezse (sunucuda sadece collected_data varsa) Route 502'ye fallback
try:
    ROUTES = _load_routes_from_gtfs()
except Exception as _gtfs_err:
    import warnings
    warnings.warn(
        f"GTFS yuklenemedi ({_gtfs_err}). Sadece Route 502 verisi kullanilacak."
    )
    ROUTES = {ROUTE_ID: {"dir0": STOPS_DIR0, "dir1": STOPS_DIR1}}

# Tum top-30 hat durak ID'leri (her iki yon, benzersiz)
ALL_ROUTE_STOP_IDS = list({
    s["stop_id"]
    for route in ROUTES.values()
    for stops in (route["dir0"], route["dir1"])
    for s in stops
})
