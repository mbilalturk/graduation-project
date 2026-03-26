"""Route 502 Data Collector - Configuration"""

# API endpoints
BASE_URL = "https://openapi.izmir.bel.tr/api/iztek"
ENDPOINT_BUS_POSITIONS = f"{BASE_URL}/hatotobuskonumlari/{{hat_id}}"
ENDPOINT_BUSES_AT_STOP = f"{BASE_URL}/duragayaklasanotobusler/{{durak_id}}"
ENDPOINT_ROUTE_BUSES_AT_STOP = f"{BASE_URL}/hattinyaklasanotobusleri/{{hat_id}}/{{durak_id}}"

# Route 502 info
ROUTE_ID = 502
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

# Collection settings
POLL_INTERVAL_SECONDS = 30
DATA_DIR = "collected_data"
