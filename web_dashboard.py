#!/usr/bin/env python3
"""
İzmir ESHOT Web Dashboard
Gerçek zamanlı otobüs takibi için web arayüzü
"""

try:
    from flask import Flask, render_template, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  Flask bulunamadı. Kurun: pip install flask flask-cors")

import pandas as pd
import json
from datetime import datetime, timedelta
import os

class IzmirBusDashboard:
    def __init__(self, data_path="./izmir_dataset/"):
        self.data_path = data_path
        self.app = None
        self.routes_data = None
        self.stops_data = None
        
        if FLASK_AVAILABLE:
            self.setup_flask_app()
        
    def setup_flask_app(self):
        """Flask uygulamasını kur"""
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/api/routes', 'get_routes', self.get_routes)
        self.app.add_url_rule('/api/stops/<route_id>', 'get_stops', self.get_stops)
        self.app.add_url_rule('/api/predictions/<route_id>/<stop_id>', 'get_predictions', self.get_predictions)
        self.app.add_url_rule('/api/live-map', 'get_live_map', self.get_live_map)
        
        print("🌐 Flask uygulaması hazırlandı")
    
    def load_data(self):
        """Veri dosyalarını yükle"""
        print("📊 Dashboard verileri yükleniyor...")
        
        try:
            # Ana veriler
            self.routes_data = pd.read_csv(f"{self.data_path}eshot-otobus-hatlari.csv", sep=';')
            self.stops_data = pd.read_csv(f"{self.data_path}eshot-otobus-duraklari.csv", sep=';')
            
            # GTFS verileri
            self.gtfs_stops = pd.read_csv(f"{self.data_path}bus-eshot-gtfs/stops.txt")
            self.gtfs_routes = pd.read_csv(f"{self.data_path}bus-eshot-gtfs/routes.txt")
            
            print("✅ Dashboard verileri yüklendi")
            return True
            
        except Exception as e:
            print(f"❌ Veri yükleme hatası: {e}")
            return False
    
    def index(self):
        """Ana sayfa"""
        return """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>İzmir ESHOT - Gerçek Zamanlı Takip</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <style>
        #map { height: 500px; }
        .prediction-card { margin: 10px 0; }
        .route-badge { margin: 2px; }
        .weather-info { background: #f8f9fa; padding: 15px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container">
                <a class="navbar-brand" href="#">🚌 İzmir ESHOT Takip</a>
                <span class="navbar-text">Hibrit LSTM ile Gerçek Zamanlı Tahmin</span>
            </div>
        </nav>
        
        <div class="row mt-3">
            <!-- Sol Panel: Kontroller -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>🎯 Otobüs Takibi</h5>
                    </div>
                    <div class="card-body">
                        <!-- Hat Seçimi -->
                        <div class="mb-3">
                            <label class="form-label">Hat Seçin:</label>
                            <select class="form-select" id="routeSelect">
                                <option value="">Hat seçin...</option>
                            </select>
                        </div>
                        
                        <!-- Durak Seçimi -->
                        <div class="mb-3">
                            <label class="form-label">Durak Seçin:</label>
                            <select class="form-select" id="stopSelect" disabled>
                                <option value="">Önce hat seçin...</option>
                            </select>
                        </div>
                        
                        <!-- Tahmin Butonu -->
                        <button class="btn btn-success w-100" id="predictBtn" disabled>
                            🔮 Varış Zamanını Tahmin Et
                        </button>
                    </div>
                </div>
                
                <!-- Tahmin Sonuçları -->
                <div class="card mt-3" id="predictionCard" style="display: none;">
                    <div class="card-header">
                        <h5>📊 Tahmin Sonuçları</h5>
                    </div>
                    <div class="card-body" id="predictionResults">
                        <!-- Dinamik içerik -->
                    </div>
                </div>
                
                <!-- Hava Durumu -->
                <div class="card mt-3">
                    <div class="card-header">
                        <h5>🌤️ Hava Durumu</h5>
                    </div>
                    <div class="card-body">
                        <div class="weather-info" id="weatherInfo">
                            <div class="text-center">
                                <div class="spinner-border" role="status">
                                    <span class="visually-hidden">Yükleniyor...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Sağ Panel: Harita -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>🗺️ İzmir Haritası</h5>
                        <small class="text-muted">Gerçek zamanlı otobüs konumları</small>
                    </div>
                    <div class="card-body">
                        <div id="map"></div>
                    </div>
                </div>
                
                <!-- İstatistikler -->
                <div class="row mt-3">
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title">441</h5>
                                <p class="card-text">Toplam Hat</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title">11,740</h5>
                                <p class="card-text">Toplam Durak</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title" id="activeBuses">-</h5>
                                <p class="card-text">Aktif Otobüs</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title" id="avgDelay">-</h5>
                                <p class="card-text">Ort. Gecikme</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <script>
        // Harita başlatma
        const map = L.map('map').setView([38.4237, 27.1428], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        // Sayfa yüklendiğinde
        document.addEventListener('DOMContentLoaded', function() {
            loadRoutes();
            loadWeatherInfo();
            startLiveUpdates();
        });
        
        // Hatları yükle
        function loadRoutes() {
            fetch('/api/routes')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('routeSelect');
                    data.routes.forEach(route => {
                        const option = document.createElement('option');
                        option.value = route.id;
                        option.textContent = `${route.id} - ${route.name}`;
                        select.appendChild(option);
                    });
                })
                .catch(error => console.error('Hatlar yüklenemedi:', error));
        }
        
        // Hat seçildiğinde durakları yükle
        document.getElementById('routeSelect').addEventListener('change', function() {
            const routeId = this.value;
            const stopSelect = document.getElementById('stopSelect');
            const predictBtn = document.getElementById('predictBtn');
            
            if (routeId) {
                fetch(`/api/stops/${routeId}`)
                    .then(response => response.json())
                    .then(data => {
                        stopSelect.innerHTML = '<option value="">Durak seçin...</option>';
                        data.stops.forEach(stop => {
                            const option = document.createElement('option');
                            option.value = stop.id;
                            option.textContent = stop.name;
                            stopSelect.appendChild(option);
                        });
                        stopSelect.disabled = false;
                    })
                    .catch(error => console.error('Duraklar yüklenemedi:', error));
            } else {
                stopSelect.innerHTML = '<option value="">Önce hat seçin...</option>';
                stopSelect.disabled = true;
                predictBtn.disabled = true;
            }
        });
        
        // Durak seçildiğinde tahmin butonunu aktifleştir
        document.getElementById('stopSelect').addEventListener('change', function() {
            const predictBtn = document.getElementById('predictBtn');
            predictBtn.disabled = !this.value;
        });
        
        // Tahmin yap
        document.getElementById('predictBtn').addEventListener('click', function() {
            const routeId = document.getElementById('routeSelect').value;
            const stopId = document.getElementById('stopSelect').value;
            
            if (routeId && stopId) {
                fetch(`/api/predictions/${routeId}/${stopId}`)
                    .then(response => response.json())
                    .then(data => {
                        showPrediction(data);
                    })
                    .catch(error => console.error('Tahmin yapılamadı:', error));
            }
        });
        
        // Tahmin sonuçlarını göster
        function showPrediction(data) {
            const card = document.getElementById('predictionCard');
            const results = document.getElementById('predictionResults');
            
            results.innerHTML = `
                <div class="alert alert-info">
                    <h6>🚌 ${data.route_name}</h6>
                    <p><strong>Durak:</strong> ${data.stop_name}</p>
                    <p><strong>Tahmini Varış:</strong> <span class="badge bg-success">${data.prediction} dakika</span></p>
                    <p><strong>Hava Etkisi:</strong> ${data.weather_impact}</p>
                    <p><strong>Güven:</strong> ${data.confidence}%</p>
                </div>
            `;
            
            card.style.display = 'block';
        }
        
        // Hava durumu bilgisini yükle
        function loadWeatherInfo() {
            // Mock hava durumu
            const weatherInfo = document.getElementById('weatherInfo');
            weatherInfo.innerHTML = `
                <div class="row text-center">
                    <div class="col-6">
                        <h4>🌤️</h4>
                        <small>Parçalı Bulutlu</small>
                    </div>
                    <div class="col-6">
                        <h4>19°C</h4>
                        <small>Nem: %65</small>
                    </div>
                </div>
            `;
        }
        
        // Canlı güncellemeler
        function startLiveUpdates() {
            // Mock veriler
            document.getElementById('activeBuses').textContent = Math.floor(Math.random() * 200 + 100);
            document.getElementById('avgDelay').textContent = (Math.random() * 5 + 1).toFixed(1) + ' dk';
            
            // Her 30 saniyede güncelle
            setInterval(() => {
                document.getElementById('activeBuses').textContent = Math.floor(Math.random() * 200 + 100);
                document.getElementById('avgDelay').textContent = (Math.random() * 5 + 1).toFixed(1) + ' dk';
            }, 30000);
        }
    </script>
</body>
</html>
        """
    
    def get_routes(self):
        """Hat listesini döndür"""
        if self.routes_data is None:
            return jsonify({"error": "Veriler yüklenmedi"}), 500
        
        routes = []
        for _, route in self.routes_data.head(20).iterrows():  # İlk 20 hat
            routes.append({
                "id": str(route['HAT_NO']),
                "name": route['HAT_ADI'],
                "description": route.get('GUZERGAH_ACIKLAMA', ''),
                "start": route.get('HAT_BASLANGIC', ''),
                "end": route.get('HAT_BITIS', '')
            })
        
        return jsonify({"routes": routes})
    
    def get_stops(self, route_id):
        """Belirli bir hattın duraklarını döndür"""
        if self.stops_data is None:
            return jsonify({"error": "Veriler yüklenmedi"}), 500
        
        # Hat ID'sine göre durakları filtrele
        route_stops = self.stops_data[
            self.stops_data['DURAKTAN_GECEN_HATLAR'].str.contains(str(route_id), na=False)
        ]
        
        stops = []
        for _, stop in route_stops.head(10).iterrows():  # İlk 10 durak
            stops.append({
                "id": str(stop['DURAK_ID']),
                "name": stop['DURAK_ADI'],
                "lat": stop['ENLEM'],
                "lon": stop['BOYLAM']
            })
        
        return jsonify({"stops": stops})
    
    def get_predictions(self, route_id, stop_id):
        """Varış zamanı tahmini döndür"""
        # Mock tahmin (gerçek uygulamada LSTM modeli kullanılacak)
        import random
        
        # Hava durumu etkisi
        weather_conditions = ['clear', 'partly_cloudy', 'overcast', 'rainy']
        weather = random.choice(weather_conditions)
        
        weather_impacts = {
            'clear': 1.0,
            'partly_cloudy': 1.05,
            'overcast': 1.10,
            'rainy': 1.25
        }
        
        base_time = random.uniform(3, 15)  # 3-15 dakika arası
        weather_factor = weather_impacts[weather]
        final_prediction = base_time * weather_factor
        
        # Route ve stop isimlerini bul
        route_name = "Bilinmiyor"
        if self.routes_data is not None:
            route_info = self.routes_data[self.routes_data['HAT_NO'].astype(str) == route_id]
            if not route_info.empty:
                route_name = route_info.iloc[0]['HAT_ADI']
        
        stop_name = "Bilinmiyor"
        if self.stops_data is not None:
            stop_info = self.stops_data[self.stops_data['DURAK_ID'].astype(str) == stop_id]
            if not stop_info.empty:
                stop_name = stop_info.iloc[0]['DURAK_ADI']
        
        return jsonify({
            "route_id": route_id,
            "route_name": route_name,
            "stop_id": stop_id,
            "stop_name": stop_name,
            "prediction": f"{final_prediction:.1f}",
            "weather_condition": weather,
            "weather_impact": f"x{weather_factor}",
            "confidence": random.randint(75, 95),
            "timestamp": datetime.now().isoformat()
        })
    
    def get_live_map(self):
        """Canlı harita verisi"""
        # Mock otobüs konumları
        buses = []
        for i in range(20):
            buses.append({
                "id": f"bus_{i}",
                "route": str(random.randint(5, 50)),
                "lat": 38.4237 + random.uniform(-0.1, 0.1),
                "lon": 27.1428 + random.uniform(-0.1, 0.1),
                "speed": random.randint(0, 60),
                "occupancy": random.randint(10, 90)
            })
        
        return jsonify({"buses": buses})
    
    def run(self, debug=True, port=8080):
        """Dashboard'ı çalıştır"""
        if not FLASK_AVAILABLE:
            print("❌ Flask kurulu değil!")
            return
        
        if not self.load_data():
            print("❌ Veriler yüklenemedi!")
            return
        
        print(f"🚀 İzmir ESHOT Dashboard başlatılıyor...")
        print(f"🌐 URL: http://localhost:{port}")
        print(f"📊 {len(self.routes_data)} hat, {len(self.stops_data)} durak yüklendi")
        
        self.app.run(debug=debug, port=port, host='0.0.0.0')

if __name__ == "__main__":
    # Dashboard'ı başlat
    dashboard = IzmirBusDashboard()
    
    if FLASK_AVAILABLE:
        dashboard.run()
    else:
        print("Flask kurulumu için: pip install flask flask-cors")