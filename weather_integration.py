#!/usr/bin/env python3
"""
İzmir ESHOT Hava Durumu Entegrasyonu
Makale referansı: Visual Crossing API kullanımı (makalede kullanılan)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import os

class IzmirWeatherIntegration:
    def __init__(self, api_key=None):
        # Visual Crossing API (makalede kullanılan)
        self.visual_crossing_key = api_key or os.getenv('VISUAL_CROSSING_API_KEY')
        
        # OpenWeatherMap alternatifi
        self.openweather_key = os.getenv('OPENWEATHER_API_KEY')
        
        # İzmir koordinatları
        self.izmir_lat = 38.4237
        self.izmir_lon = 27.1428
        
        print("🌤️  Hava durumu entegrasyonu hazırlandı")
        if not self.visual_crossing_key and not self.openweather_key:
            print("⚠️  API anahtarı bulunamadı. Çevresel değişken olarak ayarlayın:")
            print("   export VISUAL_CROSSING_API_KEY='your_key'")
            print("   export OPENWEATHER_API_KEY='your_key'")
    
    def get_visual_crossing_weather(self, date_str):
        """Visual Crossing API'den hava durumu al (makalede kullanılan)"""
        if not self.visual_crossing_key:
            return self._get_mock_weather()
        
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{self.izmir_lat},{self.izmir_lon}/{date_str}"
        
        params = {
            'key': self.visual_crossing_key,
            'include': 'hours',
            'elements': 'datetime,temp,humidity,precip,windspeed,visibility,conditions'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._process_visual_crossing_data(data)
            
        except Exception as e:
            print(f"⚠️  Visual Crossing API hatası: {e}")
            return self._get_mock_weather()
    
    def get_openweather_current(self):
        """OpenWeatherMap'ten güncel hava durumu"""
        if not self.openweather_key:
            return self._get_mock_weather()
        
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': self.izmir_lat,
            'lon': self.izmir_lon,
            'appid': self.openweather_key,
            'units': 'metric',
            'lang': 'tr'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._process_openweather_data(data)
            
        except Exception as e:
            print(f"⚠️  OpenWeatherMap API hatası: {e}")
            return self._get_mock_weather()
    
    def _process_visual_crossing_data(self, data):
        """Visual Crossing verisini işle"""
        processed = []
        
        for hour_data in data.get('days', [{}])[0].get('hours', []):
            processed.append({
                'datetime': hour_data.get('datetime'),
                'temperature': hour_data.get('temp'),
                'humidity': hour_data.get('humidity'),
                'precipitation': hour_data.get('precip', 0),
                'wind_speed': hour_data.get('windspeed'),
                'visibility': hour_data.get('visibility'),
                'conditions': hour_data.get('conditions', 'clear'),
                'weather_category': self._categorize_weather(hour_data.get('conditions', 'clear'))
            })
        
        return processed
    
    def _process_openweather_data(self, data):
        """OpenWeatherMap verisini işle"""
        return {
            'datetime': datetime.now().strftime('%H:%M:%S'),
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'precipitation': data.get('rain', {}).get('1h', 0),
            'wind_speed': data['wind']['speed'],
            'visibility': data.get('visibility', 10000) / 1000,  # km'ye çevir
            'conditions': data['weather'][0]['description'],
            'weather_category': self._categorize_weather(data['weather'][0]['main'])
        }
    
    def _categorize_weather(self, condition):
        """Hava durumunu kategorilere ayır (makaledeki gibi)"""
        condition = condition.lower()
        
        if any(word in condition for word in ['rain', 'yağmur', 'drizzle']):
            return 'rainy'
        elif any(word in condition for word in ['cloud', 'bulut', 'overcast']):
            return 'overcast'
        elif any(word in condition for word in ['partly', 'kısmen', 'scattered']):
            return 'partly_cloudy'
        else:
            return 'clear'
    
    def _get_mock_weather(self):
        """API anahtarı yokken mock veri"""
        import random
        
        categories = ['clear', 'partly_cloudy', 'overcast', 'rainy']
        
        return {
            'datetime': datetime.now().strftime('%H:%M:%S'),
            'temperature': random.uniform(10, 30),
            'humidity': random.uniform(40, 80),
            'precipitation': random.uniform(0, 5) if random.random() < 0.3 else 0,
            'wind_speed': random.uniform(0, 20),
            'visibility': random.uniform(5, 15),
            'conditions': 'Mock weather data',
            'weather_category': random.choice(categories)
        }
    
    def create_weather_features(self, datetime_obj):
        """Verilen zaman için hava durumu özelliklerini oluştur"""
        # Güncel hava durumu al
        weather_data = self.get_openweather_current()
        
        # Makaledeki özellikler
        features = {
            'temperature': weather_data['temperature'],
            'humidity': weather_data['humidity'],
            'precipitation': weather_data['precipitation'],
            'wind_speed': weather_data['wind_speed'],
            'visibility': weather_data['visibility'],
            'weather_condition': weather_data['weather_category'],
            
            # Kategorik kodlama
            'is_rainy': 1 if weather_data['weather_category'] == 'rainy' else 0,
            'is_overcast': 1 if weather_data['weather_category'] == 'overcast' else 0,
            'is_partly_cloudy': 1 if weather_data['weather_category'] == 'partly_cloudy' else 0,
            'is_clear': 1 if weather_data['weather_category'] == 'clear' else 0
        }
        
        return features
    
    def get_weather_impact_factor(self, weather_category):
        """Hava durumunun otobüs seferlerine etkisi (makaledeki bulgulara göre)"""
        impact_factors = {
            'clear': 1.0,           # Etki yok
            'partly_cloudy': 1.05,  # %5 gecikme
            'overcast': 1.10,       # %10 gecikme
            'rainy': 1.25           # %25 gecikme (makalede en yüksek)
        }
        
        return impact_factors.get(weather_category, 1.0)
    
    def create_sample_weather_dataset(self, days=7):
        """Örnek hava durumu dataset'i oluştur"""
        print(f"🌤️  {days} günlük örnek hava durumu verisi oluşturuluyor...")
        
        weather_data = []
        
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            
            for hour in range(24):
                weather_hour = date.replace(hour=hour, minute=0, second=0)
                
                # Mock veri oluştur
                weather_features = self.create_weather_features(weather_hour)
                weather_features['datetime'] = weather_hour
                weather_features['hour'] = hour
                weather_features['day'] = day
                
                weather_data.append(weather_features)
        
        # DataFrame'e çevir
        weather_df = pd.DataFrame(weather_data)
        
        # Kaydet
        weather_df.to_csv('izmir_weather_sample.csv', index=False)
        
        print(f"✅ Hava durumu verisi kaydedildi: {len(weather_df)} kayıt")
        print("📊 Özellikler:", list(weather_df.columns))
        
        return weather_df
    
    def test_apis(self):
        """API'leri test et"""
        print("🧪 Hava durumu API'leri test ediliyor...")
        
        # OpenWeatherMap test
        print("\n📡 OpenWeatherMap testi:")
        ow_data = self.get_openweather_current()
        print(f"   Sıcaklık: {ow_data['temperature']:.1f}°C")
        print(f"   Durum: {ow_data['weather_category']}")
        print(f"   Etki faktörü: {self.get_weather_impact_factor(ow_data['weather_category'])}")
        
        # Visual Crossing test (bugünün tarihi)
        print("\n📡 Visual Crossing testi:")
        today = datetime.now().strftime('%Y-%m-%d')
        vc_data = self.get_visual_crossing_weather(today)
        if isinstance(vc_data, list) and vc_data:
            print(f"   Saatlik veri sayısı: {len(vc_data)}")
            print(f"   İlk saat: {vc_data[0]['conditions']}")
        else:
            print(f"   Durum: {vc_data['weather_category']}")
        
        print("\n✅ API testleri tamamlandı!")

if __name__ == "__main__":
    # Hava durumu entegrasyonunu test et
    weather = IzmirWeatherIntegration()
    
    # API'leri test et
    weather.test_apis()
    
    # Örnek dataset oluştur
    weather.create_sample_weather_dataset(days=7)
    
    print("\n🎉 Hava durumu entegrasyonu hazır!")
    print("📋 Sonraki adım: LSTM modeli ile entegrasyon")