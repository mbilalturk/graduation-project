#!/usr/bin/env python3
"""
Kapsamlı Veri Toplama ve Temizleme Stratejisi
Bitirme Projesi - Dönem Boyunca Veri Odaklı Yaklaşım
"""

import pandas as pd
import numpy as np
import requests
import sqlite3
import schedule
import time
from datetime import datetime, timedelta
import logging
import json
import os
from pathlib import Path

class ComprehensiveDataCollector:
    def __init__(self, project_path="./bus_arrival_data/"):
        self.project_path = Path(project_path)
        self.project_path.mkdir(exist_ok=True)
        
        # Veri klasörleri
        self.raw_data_path = self.project_path / "raw_data"
        self.processed_data_path = self.project_path / "processed_data"
        self.external_data_path = self.project_path / "external_data"
        self.archive_path = self.project_path / "archive"
        
        for path in [self.raw_data_path, self.processed_data_path, 
                     self.external_data_path, self.archive_path]:
            path.mkdir(exist_ok=True)
        
        # Logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.project_path / 'data_collection.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Database setup
        self.db_path = self.project_path / "bus_data.db"
        self.init_database()
        
        print("🚀 Kapsamlı Veri Toplama Sistemi Başlatıldı")
        print(f"📂 Proje klasörü: {self.project_path}")
    
    def init_database(self):
        """Veritabanını başlat"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # İstanbul tabloları
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS istanbul_bus_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            vehicle_id TEXT,
            route_id TEXT,
            latitude REAL,
            longitude REAL,
            speed REAL,
            direction REAL,
            stop_id TEXT,
            delay_minutes REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS istanbul_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id TEXT,
            stop_id TEXT,
            scheduled_time TIME,
            actual_time TIME,
            delay_minutes REAL,
            date DATE,
            weather_condition TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # İzmir tabloları
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS izmir_gtfs_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id TEXT,
            route_id TEXT,
            stop_id TEXT,
            stop_sequence INTEGER,
            arrival_time TIME,
            departure_time TIME,
            date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Hava durumu tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            city TEXT,
            temperature REAL,
            humidity REAL,
            precipitation REAL,
            wind_speed REAL,
            visibility REAL,
            condition TEXT,
            condition_category TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Trafik verisi tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            city TEXT,
            route_segment TEXT,
            congestion_level INTEGER,
            average_speed REAL,
            travel_time_ratio REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Etkinlik verisi tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            city TEXT,
            event_type TEXT,
            event_name TEXT,
            location TEXT,
            expected_impact TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("✅ Veritabanı tabloları oluşturuldu")
    
    def collect_istanbul_data(self):
        """İstanbul IETT verilerini topla"""
        self.logger.info("📡 İstanbul IETT verisi toplanıyor...")
        
        # IETT API endpoints (Postman collection'dan)
        endpoints = {
            'bus_positions': 'https://api.ibb.gov.tr/iett/FiloDurum/SeferGerceklesme.asmx',
            'schedules': 'https://api.ibb.gov.tr/iett/UlasimAnaVeri/PlanlananSeferSaati.asmx',
            'announcements': 'https://api.ibb.gov.tr/iett/UlasimDinamikVeri/Duyurular.asmx',
            'routes': 'https://api.ibb.gov.tr/iett/UlasimAnaVeri/HatDurakGuzergah.asmx'
        }
        
        collected_data = {}
        
        for endpoint_name, url in endpoints.items():
            try:
                # SOAP request hazırla (her endpoint için özelleştirilecek)
                if endpoint_name == 'bus_positions':
                    data = self._collect_bus_positions(url)
                elif endpoint_name == 'schedules':
                    data = self._collect_schedules(url)
                elif endpoint_name == 'announcements':
                    data = self._collect_announcements(url)
                elif endpoint_name == 'routes':
                    data = self._collect_routes(url)
                
                collected_data[endpoint_name] = data
                self.logger.info(f"✅ {endpoint_name} verisi toplandı: {len(data) if data else 0} kayıt")
                
            except Exception as e:
                self.logger.error(f"❌ {endpoint_name} hatası: {str(e)}")
                collected_data[endpoint_name] = []
        
        # Veritabanına kaydet
        self._save_istanbul_data(collected_data)
        
        return collected_data
    
    def _collect_bus_positions(self, url):
        """Otobüs konumlarını topla"""
        # SOAP XML template
        soap_body = '''<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                       xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                       xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <GetFiloAracKonum_json xmlns="http://tempuri.org/" />
          </soap:Body>
        </soap:Envelope>'''
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://tempuri.org/GetFiloAracKonum_json'
        }
        
        try:
            response = requests.post(url, data=soap_body, headers=headers, timeout=30)
            response.raise_for_status()
            
            # XML response'u parse et (basitleştirilmiş)
            # Gerçek uygulamada xml.etree.ElementTree kullanılacak
            return self._parse_bus_positions(response.text)
            
        except Exception as e:
            self.logger.error(f"Bus positions API hatası: {str(e)}")
            return []
    
    def _parse_bus_positions(self, xml_response):
        """Bus position XML'ini parse et"""
        # Mock veri (gerçek uygulamada XML parsing)
        import random
        
        positions = []
        for i in range(50):  # 50 otobüs simüle et
            positions.append({
                'vehicle_id': f'bus_{i:03d}',
                'route_id': str(random.randint(5, 500)),
                'latitude': 41.0082 + random.uniform(-0.1, 0.1),
                'longitude': 28.9784 + random.uniform(-0.1, 0.1),
                'speed': random.randint(0, 60),
                'direction': random.randint(0, 360),
                'timestamp': datetime.now()
            })
        
        return positions
    
    def collect_weather_data(self, cities=['Istanbul', 'Izmir']):
        """Hava durumu verisi topla"""
        self.logger.info(f"🌤️ Hava durumu verisi toplanıyor: {cities}")
        
        weather_data = []
        
        for city in cities:
            try:
                # OpenWeatherMap API (gerçek API key gerekli)
                api_key = os.getenv('OPENWEATHER_API_KEY')
                if not api_key:
                    # Mock veri
                    weather_info = self._get_mock_weather(city)
                else:
                    weather_info = self._get_real_weather(city, api_key)
                
                weather_data.append(weather_info)
                
            except Exception as e:
                self.logger.error(f"Hava durumu hatası ({city}): {str(e)}")
        
        # Veritabanına kaydet
        self._save_weather_data(weather_data)
        
        return weather_data
    
    def _get_mock_weather(self, city):
        """Mock hava durumu verisi"""
        import random
        
        conditions = ['clear', 'partly_cloudy', 'overcast', 'rainy']
        
        return {
            'city': city,
            'timestamp': datetime.now(),
            'temperature': random.uniform(5, 35),
            'humidity': random.uniform(30, 90),
            'precipitation': random.uniform(0, 10) if random.random() < 0.3 else 0,
            'wind_speed': random.uniform(0, 25),
            'visibility': random.uniform(5, 15),
            'condition': random.choice(['Clear', 'Clouds', 'Rain', 'Snow']),
            'condition_category': random.choice(conditions)
        }
    
    def collect_traffic_data(self):
        """Trafik verisi topla"""
        self.logger.info("🚗 Trafik verisi toplanıyor...")
        
        # Google Maps Traffic API, HERE API, vs. entegrasyonu
        # Şimdilik mock veri
        traffic_data = []
        
        routes = ['D100', 'TEM', 'E5', 'Bosphorus Bridge', 'FSM Bridge']
        
        for route in routes:
            traffic_info = {
                'route_segment': route,
                'city': 'Istanbul',
                'timestamp': datetime.now(),
                'congestion_level': np.random.randint(1, 6),  # 1-5 arası
                'average_speed': np.random.uniform(20, 80),
                'travel_time_ratio': np.random.uniform(1.0, 3.0)  # Normal süreye oran
            }
            traffic_data.append(traffic_info)
        
        self._save_traffic_data(traffic_data)
        return traffic_data
    
    def collect_event_data(self):
        """Etkinlik verisi topla"""
        self.logger.info("🎉 Etkinlik verisi toplanıyor...")
        
        # Eventbrite API, Biletix API, belediye duyuruları vs.
        # Şimdilik mock veri
        events = [
            {
                'date': datetime.now().date(),
                'city': 'Istanbul',
                'event_type': 'Concert',
                'event_name': 'Rock Concert at Zorlu',
                'location': 'Zorlu Center',
                'expected_impact': 'High traffic in Besiktas area'
            },
            {
                'date': datetime.now().date() + timedelta(days=1),
                'city': 'Istanbul',
                'event_type': 'Sports',
                'event_name': 'Galatasaray vs Fenerbahce',
                'location': 'Turk Telekom Stadium',
                'expected_impact': 'Heavy traffic around stadium'
            }
        ]
        
        self._save_event_data(events)
        return events
    
    def _save_istanbul_data(self, data):
        """İstanbul verisini veritabanına kaydet"""
        conn = sqlite3.connect(self.db_path)
        
        # Bus positions
        if data.get('bus_positions'):
            df = pd.DataFrame(data['bus_positions'])
            df.to_sql('istanbul_bus_positions', conn, if_exists='append', index=False)
        
        conn.close()
    
    def _save_weather_data(self, data):
        """Hava durumu verisini kaydet"""
        if not data:
            return
        
        conn = sqlite3.connect(self.db_path)
        df = pd.DataFrame(data)
        df.to_sql('weather_data', conn, if_exists='append', index=False)
        conn.close()
    
    def _save_traffic_data(self, data):
        """Trafik verisini kaydet"""
        if not data:
            return
        
        conn = sqlite3.connect(self.db_path)
        df = pd.DataFrame(data)
        df.to_sql('traffic_data', conn, if_exists='append', index=False)
        conn.close()
    
    def _save_event_data(self, data):
        """Etkinlik verisini kaydet"""
        if not data:
            return
        
        conn = sqlite3.connect(self.db_path)
        df = pd.DataFrame(data)
        df.to_sql('event_data', conn, if_exists='append', index=False)
        conn.close()
    
    def run_data_collection_cycle(self):
        """Tam veri toplama döngüsü"""
        self.logger.info("🔄 Veri toplama döngüsü başlıyor...")
        
        start_time = datetime.now()
        
        # Tüm veri kaynaklarını topla
        istanbul_data = self.collect_istanbul_data()
        weather_data = self.collect_weather_data()
        traffic_data = self.collect_traffic_data()
        event_data = self.collect_event_data()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # İstatistikleri logla
        stats = {
            'cycle_duration': duration,
            'istanbul_records': len(istanbul_data.get('bus_positions', [])),
            'weather_records': len(weather_data),
            'traffic_records': len(traffic_data),
            'event_records': len(event_data),
            'timestamp': datetime.now()
        }
        
        self.logger.info(f"✅ Veri toplama tamamlandı: {duration:.1f}s")
        self.logger.info(f"📊 İstatistikler: {stats}")
        
        return stats
    
    def schedule_data_collection(self):
        """Otomatik veri toplama zamanlaması"""
        self.logger.info("⏰ Otomatik veri toplama zamanlanıyor...")
        
        # Her 5 dakikada otobüs konumları
        schedule.every(5).minutes.do(self.collect_istanbul_data)
        
        # Her saatte hava durumu
        schedule.every().hour.do(self.collect_weather_data)
        
        # Her 15 dakikada trafik
        schedule.every(15).minutes.do(self.collect_traffic_data)
        
        # Günde bir etkinlik
        schedule.every().day.at("06:00").do(self.collect_event_data)
        
        print("📅 Zamanlama ayarlandı:")
        print("  - Otobüs konumları: Her 5 dakika")
        print("  - Hava durumu: Her saat")
        print("  - Trafik: Her 15 dakika")
        print("  - Etkinlikler: Günlük 06:00")
        
        # Sürekli çalıştır
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1 dakika bekle
    
    def generate_data_quality_report(self):
        """Veri kalitesi raporu oluştur"""
        self.logger.info("📋 Veri kalitesi raporu oluşturuluyor...")
        
        conn = sqlite3.connect(self.db_path)
        
        report = {
            'timestamp': datetime.now(),
            'tables': {}
        }
        
        # Her tablo için istatistikler
        tables = ['istanbul_bus_positions', 'weather_data', 'traffic_data', 'event_data']
        
        for table in tables:
            try:
                # Kayıt sayısı
                count_query = f"SELECT COUNT(*) FROM {table}"
                count = pd.read_sql_query(count_query, conn).iloc[0, 0]
                
                # Son kayıt zamanı
                latest_query = f"SELECT MAX(created_at) FROM {table}"
                latest = pd.read_sql_query(latest_query, conn).iloc[0, 0]
                
                # Bugünkü kayıtlar
                today_query = f"SELECT COUNT(*) FROM {table} WHERE DATE(created_at) = DATE('now')"
                today_count = pd.read_sql_query(today_query, conn).iloc[0, 0]
                
                report['tables'][table] = {
                    'total_records': count,
                    'latest_record': latest,
                    'today_records': today_count
                }
                
            except Exception as e:
                self.logger.error(f"Tablo {table} rapor hatası: {str(e)}")
                report['tables'][table] = {'error': str(e)}
        
        conn.close()
        
        # Raporu kaydet
        report_path = self.project_path / f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str, ensure_ascii=False)
        
        self.logger.info(f"✅ Veri kalitesi raporu kaydedildi: {report_path}")
        
        return report

if __name__ == "__main__":
    # Kapsamlı veri toplama sistemini başlat
    collector = ComprehensiveDataCollector()
    
    print("\n🎯 VERİ TOPLAMA STRATEJİSİ")
    print("="*50)
    print("1. 📡 İstanbul IETT API'leri (gerçek zamanlı)")
    print("2. 📊 İzmir GTFS verileri (statik)")
    print("3. 🌤️  Hava durumu (saatlik)")
    print("4. 🚗 Trafik verileri (15 dakikalık)")
    print("5. 🎉 Etkinlik verileri (günlük)")
    print("="*50)
    
    # İlk veri toplama döngüsü
    collector.run_data_collection_cycle()
    
    # Veri kalitesi raporu
    report = collector.generate_data_quality_report()
    print(f"\n📋 Veri Kalitesi Raporu:")
    for table, stats in report['tables'].items():
        if 'error' not in stats:
            print(f"  {table}: {stats['total_records']} kayıt, son: {stats['latest_record']}")
    
    print("\n🔄 Sürekli veri toplama için:")
    print("  python comprehensive_data_strategy.py --schedule")