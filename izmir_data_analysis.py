#!/usr/bin/env python3
"""
İzmir ESHOT Dataset Analizi
Makale: Spatio-Temporal Forecasting of Bus Arrival Times Using Context-Aware Deep Learning Models
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class IzmirDataAnalyzer:
    def __init__(self, data_path="./izmir_dataset/"):
        self.data_path = data_path
        self.routes = None
        self.stops = None
        self.schedules = None
        self.gtfs_stops = None
        self.gtfs_stop_times = None
        
    def load_data(self):
        """Tüm veri dosyalarını yükle"""
        print("📊 İzmir ESHOT verilerini yüklüyor...")
        
        # CSV dosyaları
        self.routes = pd.read_csv(f"{self.data_path}eshot-otobus-hatlari.csv", sep=';')
        self.stops = pd.read_csv(f"{self.data_path}eshot-otobus-duraklari.csv", sep=';')
        self.schedules = pd.read_csv(f"{self.data_path}eshot-otobus-hareketsaatleri.csv", sep=';')
        
        # GTFS dosyaları
        self.gtfs_stops = pd.read_csv(f"{self.data_path}bus-eshot-gtfs/stops.txt")
        self.gtfs_stop_times = pd.read_csv(f"{self.data_path}bus-eshot-gtfs/stop_times.txt")
        
        print("✅ Veriler başarıyla yüklendi!")
        return self
    
    def basic_statistics(self):
        """Temel istatistikler"""
        print("\n" + "="*50)
        print("📈 TEMEL İSTATİSTİKLER")
        print("="*50)
        
        print(f"🚌 Toplam Hat Sayısı: {len(self.routes):,}")
        print(f"🚏 Toplam Durak Sayısı: {len(self.stops):,}")
        print(f"⏰ Toplam Sefer Sayısı: {len(self.schedules):,}")
        print(f"📍 GTFS Durak Sayısı: {len(self.gtfs_stops):,}")
        print(f"🕐 GTFS Durak Zamanı: {len(self.gtfs_stop_times):,}")
        
        # Hat başına ortalama durak sayısı
        stops_per_route = self.stops['DURAKTAN_GECEN_HATLAR'].str.split('-').str.len().mean()
        print(f"📊 Hat başına ortalama durak: {stops_per_route:.1f}")
        
        return self
    
    def route_analysis(self):
        """Hat analizi"""
        print("\n" + "="*50)
        print("🚌 HAT ANALİZİ")
        print("="*50)
        
        # En popüler hatlar (durak sayısına göre)
        route_popularity = {}
        for _, row in self.stops.iterrows():
            routes_str = str(row['DURAKTAN_GECEN_HATLAR'])
            if routes_str != 'nan':
                routes = routes_str.split('-')
                for route in routes:
                    route = route.strip()
                    route_popularity[route] = route_popularity.get(route, 0) + 1
        
        # En çok duraktan geçen 10 hat
        top_routes = sorted(route_popularity.items(), key=lambda x: x[1], reverse=True)[:10]
        print("🔥 En çok duraktan geçen hatlar:")
        for i, (route, count) in enumerate(top_routes, 1):
            route_name = self.routes[self.routes['HAT_NO'].astype(str) == route]['HAT_ADI'].iloc[0] if len(self.routes[self.routes['HAT_NO'].astype(str) == route]) > 0 else "Bilinmiyor"
            print(f"  {i:2d}. Hat {route}: {count:3d} durak - {route_name}")
        
        return self
    
    def schedule_analysis(self):
        """Sefer saatleri analizi"""
        print("\n" + "="*50)
        print("⏰ SEFER SAATLERİ ANALİZİ")
        print("="*50)
        
        # Saatlik dağılım
        self.schedules['GIDIS_SAAT'] = pd.to_datetime(self.schedules['GIDIS_SAATI'], format='%H:%M').dt.hour
        hourly_dist = self.schedules['GIDIS_SAAT'].value_counts().sort_index()
        
        print("📊 Saatlik sefer dağılımı:")
        for hour, count in hourly_dist.head(10).items():
            print(f"  {int(hour):02d}:00 - {count:,} sefer")
        
        # Peak saatler
        peak_morning = hourly_dist[6:10].sum()
        peak_evening = hourly_dist[17:20].sum()
        off_peak = hourly_dist.sum() - peak_morning - peak_evening
        
        print(f"\n🌅 Sabah peak (06-10): {peak_morning:,} sefer ({peak_morning/hourly_dist.sum()*100:.1f}%)")
        print(f"🌆 Akşam peak (17-20): {peak_evening:,} sefer ({peak_evening/hourly_dist.sum()*100:.1f}%)")
        print(f"🕐 Normal saatler: {off_peak:,} sefer ({off_peak/hourly_dist.sum()*100:.1f}%)")
        
        return self
    
    def gtfs_analysis(self):
        """GTFS veri analizi"""
        print("\n" + "="*50)
        print("📋 GTFS VERİ ANALİZİ")
        print("="*50)
        
        # Stop times analizi
        sample_trip = self.gtfs_stop_times['trip_id'].iloc[0]
        trip_stops = self.gtfs_stop_times[self.gtfs_stop_times['trip_id'] == sample_trip]
        
        print(f"🚌 Örnek sefer ({sample_trip}):")
        print(f"  - Durak sayısı: {len(trip_stops)}")
        print(f"  - İlk durak: {trip_stops['arrival_time'].iloc[0]}")
        print(f"  - Son durak: {trip_stops['arrival_time'].iloc[-1]}")
        
        # Toplam sefer sayısı
        total_trips = self.gtfs_stop_times['trip_id'].nunique()
        print(f"\n📊 Toplam benzersiz sefer: {total_trips:,}")
        
        return self
    
    def data_quality_check(self):
        """Veri kalitesi kontrolü"""
        print("\n" + "="*50)
        print("🔍 VERİ KALİTESİ KONTROLÜ")
        print("="*50)
        
        datasets = {
            'Hatlar': self.routes,
            'Duraklar': self.stops,
            'Sefer Saatleri': self.schedules,
            'GTFS Duraklar': self.gtfs_stops,
            'GTFS Zamanlar': self.gtfs_stop_times
        }
        
        for name, df in datasets.items():
            missing_pct = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
            print(f"📋 {name}:")
            print(f"  - Boyut: {df.shape[0]:,} x {df.shape[1]}")
            print(f"  - Eksik veri: {missing_pct:.2f}%")
            print(f"  - Bellek kullanımı: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        
        return self
    
    def generate_features_for_ml(self):
        """Makine öğrenmesi için özellik çıkarımı"""
        print("\n" + "="*50)
        print("🤖 MAKİNE ÖĞRENMESİ ÖZELLİKLERİ")
        print("="*50)
        
        # Zaman blokları (makaledeki gibi)
        def get_time_block(hour):
            if 6 <= hour < 10:
                return 'morning_peak'
            elif 17 <= hour < 20:
                return 'evening_peak'
            elif 22 <= hour or hour < 6:
                return 'night'
            else:
                return 'off_peak'
        
        # Örnek özellik seti
        if hasattr(self.schedules, 'GIDIS_SAAT'):
            self.schedules['time_block'] = self.schedules['GIDIS_SAAT'].apply(get_time_block)
            time_block_dist = self.schedules['time_block'].value_counts()
            
            print("⏰ Zaman bloklarına göre dağılım:")
            for block, count in time_block_dist.items():
                print(f"  {block}: {count:,} sefer ({count/len(self.schedules)*100:.1f}%)")
        
        # GPS koordinat analizi
        lat_range = self.stops['ENLEM'].max() - self.stops['ENLEM'].min()
        lon_range = self.stops['BOYLAM'].max() - self.stops['BOYLAM'].min()
        
        print(f"\n📍 Coğrafi kapsam:")
        print(f"  Enlem aralığı: {lat_range:.4f}° ({lat_range*111:.1f} km)")
        print(f"  Boylam aralığı: {lon_range:.4f}° ({lon_range*111*np.cos(np.radians(38.4)):.1f} km)")
        
        return self
    
    def create_sample_ml_dataset(self):
        """Örnek ML dataset'i oluştur"""
        print("\n" + "="*50)
        print("📊 ÖRNEK ML DATASET'İ OLUŞTURULUYOR")
        print("="*50)
        
        # GTFS stop_times'dan örnek dataset
        sample_data = self.gtfs_stop_times.head(1000).copy()
        
        # Zaman özelliklerini çıkar
        sample_data['hour'] = pd.to_datetime(sample_data['arrival_time'], format='%H:%M:%S').dt.hour
        sample_data['minute'] = pd.to_datetime(sample_data['arrival_time'], format='%H:%M:%S').dt.minute
        
        # Zaman blokları
        sample_data['time_block'] = sample_data['hour'].apply(
            lambda h: 'morning_peak' if 6 <= h < 10 
            else 'evening_peak' if 17 <= h < 20 
            else 'night' if h >= 22 or h < 6 
            else 'off_peak'
        )
        
        # Seyahat süresi (hedef değişken)
        sample_data['travel_time'] = (
            pd.to_datetime(sample_data['departure_time'], format='%H:%M:%S') - 
            pd.to_datetime(sample_data['arrival_time'], format='%H:%M:%S')
        ).dt.total_seconds() / 60  # dakika cinsinden
        
        # Örnek kaydet
        sample_data[['trip_id', 'stop_id', 'stop_sequence', 'hour', 'minute', 'time_block', 'travel_time']].to_csv(
            'izmir_sample_ml_data.csv', index=False
        )
        
        print("✅ Örnek ML dataset'i 'izmir_sample_ml_data.csv' olarak kaydedildi")
        print(f"📊 Boyut: {len(sample_data)} satır")
        print(f"🎯 Özellikler: trip_id, stop_id, stop_sequence, hour, minute, time_block, travel_time")
        
        return self
    
    def run_full_analysis(self):
        """Tam analizi çalıştır"""
        print("🚀 İzmir ESHOT Dataset Analizi Başlıyor...")
        print("Makale referansı: Spatio-Temporal Forecasting of Bus Arrival Times")
        
        (self.load_data()
         .basic_statistics()
         .route_analysis()
         .schedule_analysis()
         .gtfs_analysis()
         .data_quality_check()
         .generate_features_for_ml()
         .create_sample_ml_dataset())
        
        print("\n" + "="*50)
        print("🎉 ANALİZ TAMAMLANDI!")
        print("="*50)
        print("📋 Sonraki adımlar:")
        print("  1. Hava durumu API'si entegrasyonu")
        print("  2. Hibrit LSTM modeli geliştirme")
        print("  3. Gerçek zamanlı tahmin sistemi")
        print("  4. Web dashboard oluşturma")
        
        return self

if __name__ == "__main__":
    analyzer = IzmirDataAnalyzer()
    analyzer.run_full_analysis()