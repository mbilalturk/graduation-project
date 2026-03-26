"""
Trip Extractor - Toplanan gercek zamanli veriden seyahat surelerini cikarir.

Collector tarafindan toplanan ham GPS verisini analiz ederek:
1. Her otobusun her seferini (trip) tespit eder
2. Duraklar arasi gercek seyahat surelerini hesaplar
3. GTFS planlanmis surelerle karsilastirir
4. ML icin hazir dataset olusturur

Kullanim:
    python trip_extractor.py                    # Tum veriyi isle
    python trip_extractor.py --date 2026-03-26  # Belirli gun
    python trip_extractor.py --stats            # Istatistik goster
"""

import argparse
import csv
import math
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

from config import STOPS_DIR0, STOPS_DIR1, DATA_DIR, ROUTE_ID

DB_PATH = os.path.join(DATA_DIR, "route_502_realtime.db")
OUTPUT_DIR = os.path.join(DATA_DIR, "extracted_trips")


def get_db():
    return sqlite3.connect(DB_PATH)


def extract_trips(date_filter=None):
    """
    bus_positions tablosundan otobus hareketlerini analiz ederek
    trip'leri ve duraklar arasi seyahat surelerini cikarir.
    """
    conn = get_db()
    conn.row_factory = sqlite3.Row

    query = """
        SELECT timestamp, otobus_id, yon, lat, lon,
               nearest_stop_id, nearest_stop_seq, distance_to_nearest_m
        FROM bus_positions
        WHERE nearest_stop_id IS NOT NULL
          AND distance_to_nearest_m < 100
    """
    params = []
    if date_filter:
        query += " AND timestamp LIKE ?"
        params.append(f"{date_filter}%")

    query += " ORDER BY otobus_id, yon, timestamp"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("Veri bulunamadi.")
        return []

    print(f"Isleniyor: {len(rows)} konum kaydi")

    # Otobus + yon bazinda grupla
    bus_tracks = defaultdict(list)
    for row in rows:
        key = (row["otobus_id"], row["yon"])
        bus_tracks[key].append(dict(row))

    trips = []

    for (bus_id, yon), track in bus_tracks.items():
        stops_list = STOPS_DIR0 if yon == 0 else STOPS_DIR1
        max_seq = max(s["seq"] for s in stops_list)

        # Trip'leri ayir: seq azalirsa veya buyuk bosluk varsa yeni trip
        current_trip = []
        prev_seq = -1
        prev_time = None

        for point in track:
            ts = datetime.strptime(point["timestamp"], "%Y-%m-%d %H:%M:%S")
            seq = point["nearest_stop_seq"]

            new_trip = False
            if prev_time and (ts - prev_time).total_seconds() > 1800:
                # 30 dk'dan fazla bosluk = yeni trip
                new_trip = True
            elif yon == 0 and seq < prev_seq - 2:
                # Gidis yonunde seq geri gidiyorsa yeni trip
                new_trip = True
            elif yon == 1 and seq < prev_seq - 2:
                new_trip = True

            if new_trip and current_trip:
                trips.append(build_trip_record(bus_id, yon, current_trip))
                current_trip = []

            current_trip.append({
                "timestamp": ts,
                "stop_id": point["nearest_stop_id"],
                "stop_seq": seq,
                "lat": point["lat"],
                "lon": point["lon"],
                "distance_m": point["distance_to_nearest_m"],
            })
            prev_seq = seq
            prev_time = ts

        if current_trip:
            trips.append(build_trip_record(bus_id, yon, current_trip))

    print(f"Toplam {len(trips)} trip tespit edildi.")
    return trips


def build_trip_record(bus_id, yon, points):
    """Bir trip icin duraklar arasi seyahat surelerini hesapla."""
    # Her durak icin ilk gorus zamanini bul
    stop_first_seen = {}
    for p in points:
        seq = p["stop_seq"]
        if seq not in stop_first_seen:
            stop_first_seen[seq] = p["timestamp"]

    sorted_seqs = sorted(stop_first_seen.keys())

    segments = []
    for i in range(1, len(sorted_seqs)):
        from_seq = sorted_seqs[i - 1]
        to_seq = sorted_seqs[i]
        t_from = stop_first_seen[from_seq]
        t_to = stop_first_seen[to_seq]
        travel_seconds = (t_to - t_from).total_seconds()
        travel_minutes = travel_seconds / 60.0

        # Saçma değerleri filtrele
        if travel_minutes < 0 or travel_minutes > 30:
            continue

        segments.append({
            "from_seq": from_seq,
            "to_seq": to_seq,
            "travel_seconds": travel_seconds,
            "travel_minutes": round(travel_minutes, 2),
        })

    start_time = points[0]["timestamp"]
    end_time = points[-1]["timestamp"]
    total_minutes = (end_time - start_time).total_seconds() / 60.0

    return {
        "bus_id": bus_id,
        "yon": yon,
        "date": start_time.strftime("%Y-%m-%d"),
        "start_time": start_time.strftime("%H:%M:%S"),
        "end_time": end_time.strftime("%H:%M:%S"),
        "total_minutes": round(total_minutes, 2),
        "stops_observed": len(stop_first_seen),
        "segments": segments,
        "hour": start_time.hour,
        "day_of_week": start_time.weekday(),  # 0=Mon, 6=Sun
    }


def export_segments_csv(trips, output_path=None):
    """Duraklar arasi seyahat surelerini CSV'ye aktar (ML icin)."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, "route_502_segments.csv")

    fieldnames = [
        "date", "bus_id", "yon", "trip_start_time", "hour", "day_of_week",
        "from_stop_seq", "to_stop_seq", "travel_seconds", "travel_minutes",
    ]

    rows = []
    for trip in trips:
        for seg in trip["segments"]:
            rows.append({
                "date": trip["date"],
                "bus_id": trip["bus_id"],
                "yon": trip["yon"],
                "trip_start_time": trip["start_time"],
                "hour": trip["hour"],
                "day_of_week": trip["day_of_week"],
                "from_stop_seq": seg["from_seq"],
                "to_stop_seq": seg["to_seq"],
                "travel_seconds": seg["travel_seconds"],
                "travel_minutes": seg["travel_minutes"],
            })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV exported: {output_path} ({len(rows)} segments)")
    return output_path


def export_trips_csv(trips, output_path=None):
    """Trip ozet bilgilerini CSV'ye aktar."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, "route_502_trips.csv")

    fieldnames = [
        "date", "bus_id", "yon", "start_time", "end_time",
        "total_minutes", "stops_observed", "hour", "day_of_week",
    ]

    rows = []
    for trip in trips:
        rows.append({
            "date": trip["date"],
            "bus_id": trip["bus_id"],
            "yon": trip["yon"],
            "start_time": trip["start_time"],
            "end_time": trip["end_time"],
            "total_minutes": trip["total_minutes"],
            "stops_observed": trip["stops_observed"],
            "hour": trip["hour"],
            "day_of_week": trip["day_of_week"],
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV exported: {output_path} ({len(rows)} trips)")
    return output_path


def show_stats():
    """Veritabanindaki veri istatistiklerini goster."""
    conn = get_db()

    tables = {
        "bus_positions": "Otobus konum kaydi",
        "stop_arrivals": "Durak yaklasma kaydi",
        "trip_events": "Durak gecis olaylari",
    }

    print("=== Veritabani Istatistikleri ===\n")
    for table, desc in tables.items():
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{desc} ({table}): {count:,} kayit")

        if count > 0:
            first = conn.execute(f"SELECT MIN(timestamp) FROM {table}").fetchone()[0]
            last = conn.execute(f"SELECT MAX(timestamp) FROM {table}").fetchone()[0]
            print(f"  Zaman araligi: {first} -> {last}")

            if table == "bus_positions":
                buses = conn.execute(
                    "SELECT COUNT(DISTINCT otobus_id) FROM bus_positions"
                ).fetchone()[0]
                polls = conn.execute(
                    "SELECT COUNT(DISTINCT poll_id) FROM bus_positions"
                ).fetchone()[0]
                print(f"  Benzersiz otobus: {buses}, Toplam poll: {polls}")
        print()

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Route 502 Trip Extractor")
    parser.add_argument("--date", type=str, default=None, help="Tarih filtresi (YYYY-MM-DD)")
    parser.add_argument("--stats", action="store_true", help="Istatistikleri goster")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    else:
        trips = extract_trips(args.date)
        if trips:
            export_segments_csv(trips)
            export_trips_csv(trips)
