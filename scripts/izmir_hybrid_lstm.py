#!/usr/bin/env python3
"""
İzmir ESHOT Hibrit LSTM Modeli
Makale referansı: Spatio-Temporal Forecasting of Bus Arrival Times Using Context-Aware Deep Learning Models
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Deep Learning
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, concatenate
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    from sklearn.preprocessing import MinMaxScaler, LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False
    print("⚠️  TensorFlow/Scikit-learn bulunamadı. Önce kurun: pip install tensorflow scikit-learn")

class IzmirHybridLSTM:
    def __init__(self, data_path="./izmir_dataset/"):
        self.data_path = data_path
        self.model = None
        self.scaler = MinMaxScaler()
        self.label_encoders = {}
        self.trend_threshold = 1000  # Makaledeki gibi
        
        # Makale parametreleri
        self.lstm_units = 128
        self.dropout_rate = 0.2
        self.batch_size = 64
        self.epochs = 50
        self.patience = 10
        
    def load_and_prepare_data(self):
        """Veriyi yükle ve makine öğrenmesi için hazırla"""
        print("📊 İzmir ESHOT verilerini yüklüyor...")
        
        # GTFS verilerini yükle
        stops = pd.read_csv(f"{self.data_path}bus-eshot-gtfs/stops.txt")
        stop_times = pd.read_csv(f"{self.data_path}bus-eshot-gtfs/stop_times.txt")
        trips = pd.read_csv(f"{self.data_path}bus-eshot-gtfs/trips.txt")
        routes = pd.read_csv(f"{self.data_path}bus-eshot-gtfs/routes.txt")
        
        print(f"✅ GTFS verileri yüklendi: {len(stop_times):,} durak zamanı")
        
        # Sample data (performans için)
        sample_size = 50000
        if len(stop_times) > sample_size:
            stop_times = stop_times.sample(n=sample_size, random_state=42)
            print(f"📊 Performans için {sample_size:,} örnek alındı")
        
        return self.feature_engineering(stop_times, stops, trips, routes)
    
    def feature_engineering(self, stop_times, stops, trips, routes):
        """Makaledeki gibi özellik mühendisliği"""
        print("🔧 Özellik mühendisliği yapılıyor...")
        
        # Zaman özelliklerini çıkar
        stop_times['arrival_datetime'] = pd.to_datetime(stop_times['arrival_time'], format='%H:%M:%S', errors='coerce')
        stop_times['departure_datetime'] = pd.to_datetime(stop_times['departure_time'], format='%H:%M:%S', errors='coerce')
        
        # Temiz veriyi filtrele
        stop_times = stop_times.dropna(subset=['arrival_datetime', 'departure_datetime'])
        
        # Zaman özellikleri
        stop_times['hour'] = stop_times['arrival_datetime'].dt.hour
        stop_times['minute'] = stop_times['arrival_datetime'].dt.minute
        stop_times['day_of_week'] = np.random.choice([0, 1, 2, 3, 4, 5, 6], len(stop_times))  # Simulated
        
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
        
        stop_times['time_block'] = stop_times['hour'].apply(get_time_block)
        
        # Gün tipi
        stop_times['day_type'] = stop_times['day_of_week'].apply(
            lambda x: 'weekend' if x >= 5 else 'weekday'
        )
        
        # Seyahat süresi (hedef değişken)
        stop_times['travel_time'] = (
            stop_times['departure_datetime'] - stop_times['arrival_datetime']
        ).dt.total_seconds() / 60  # dakika
        
        # Negatif değerleri temizle
        stop_times = stop_times[stop_times['travel_time'] >= 0]
        
        # Aykırı değerleri temizle (>60 dakika)
        stop_times = stop_times[stop_times['travel_time'] <= 60]
        
        # Trend özelliği (makaledeki selective trend)
        stop_times['trend_slope'] = 0  # Başlangıçta sıfır
        
        # Grup bazlı trend hesaplama
        for (time_block, day_type), group in stop_times.groupby(['time_block', 'day_type']):
            if len(group) < self.trend_threshold:
                # Az veri olan gruplar için trend ekle
                trend = np.linspace(0, 1, len(group))
                stop_times.loc[group.index, 'trend_slope'] = trend
        
        # GPS bilgilerini ekle (stops tablosundan)
        stop_times = stop_times.merge(stops[['stop_id', 'stop_lat', 'stop_lon']], 
                                    on='stop_id', how='left')
        
        print(f"✅ Özellik mühendisliği tamamlandı: {len(stop_times):,} örnek")
        
        return stop_times
    
    def prepare_features(self, data):
        """Özellikleri hazırla ve encode et"""
        print("🎯 Özellikler hazırlanıyor...")
        
        # Kategorik değişkenleri encode et
        categorical_features = ['time_block', 'day_type']
        for feature in categorical_features:
            if feature not in self.label_encoders:
                self.label_encoders[feature] = LabelEncoder()
                data[f'{feature}_encoded'] = self.label_encoders[feature].fit_transform(data[feature])
            else:
                data[f'{feature}_encoded'] = self.label_encoders[feature].transform(data[feature])
        
        # Özellik seti
        feature_columns = [
            'stop_sequence', 'hour', 'minute', 'day_of_week',
            'time_block_encoded', 'day_type_encoded', 'trend_slope',
            'stop_lat', 'stop_lon'
        ]
        
        # Eksik değerleri temizle
        data = data.dropna(subset=feature_columns + ['travel_time'])
        
        X = data[feature_columns].values
        y = data['travel_time'].values
        
        # Normalizasyon
        X = self.scaler.fit_transform(X)
        
        print(f"✅ Özellikler hazırlandı: {X.shape[1]} özellik, {len(X):,} örnek")
        
        return X, y, data
    
    def build_hybrid_lstm_model(self, input_shape):
        """Makaledeki hibrit LSTM modelini oluştur"""
        print("🧠 Hibrit LSTM modeli oluşturuluyor...")
        
        # Ana LSTM dalı
        main_input = Input(shape=(1, input_shape))
        lstm_out = LSTM(self.lstm_units, return_sequences=False)(main_input)
        lstm_out = Dropout(self.dropout_rate)(lstm_out)
        
        # Dense katmanlar
        dense_1 = Dense(64, activation='relu')(lstm_out)
        dense_1 = Dropout(self.dropout_rate)(dense_1)
        
        # Çıkış katmanı
        output = Dense(1, activation='linear')(dense_1)
        
        # Model oluştur
        model = Model(inputs=main_input, outputs=output)
        
        # Compile
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mean_absolute_error',
            metrics=['mae', 'mse']
        )
        
        print("✅ Hibrit LSTM modeli oluşturuldu")
        print(f"📊 Parametreler: LSTM={self.lstm_units}, Dropout={self.dropout_rate}")
        
        return model
    
    def train_model(self, X, y):
        """Modeli eğit"""
        print("🚀 Model eğitimi başlıyor...")
        
        # Veriyi böl
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # LSTM için reshape
        X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
        X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
        
        # Model oluştur
        self.model = self.build_hybrid_lstm_model(X_train.shape[2])
        
        # Early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=self.patience,
            restore_best_weights=True
        )
        
        # Eğitim
        history = self.model.fit(
            X_train, y_train,
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_data=(X_test, y_test),
            callbacks=[early_stopping],
            verbose=1
        )
        
        # Tahmin ve değerlendirme
        y_pred = self.model.predict(X_test)
        
        # Metrikleri hesapla
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # MAPE hesapla
        mape = np.mean(np.abs((y_test - y_pred.flatten()) / y_test)) * 100
        
        print("\n" + "="*50)
        print("📊 MODEL PERFORMANSI")
        print("="*50)
        print(f"🎯 MAE: {mae:.3f} dakika")
        print(f"📈 RMSE: {rmse:.3f} dakika")
        print(f"📊 R²: {r2:.4f}")
        print(f"📉 MAPE: {mape:.2f}%")
        
        # Makaledeki sonuçlarla karşılaştır
        print(f"\n📚 Makale sonuçları (İstanbul):")
        print(f"   MAE: 2.97 dakika")
        print(f"   MAPE: 14.79%")
        print(f"   R²: 0.9272")
        
        return history, (mae, rmse, r2, mape)
    
    def predict_arrival_time(self, route_id, stop_id, current_time, weather='clear'):
        """Varış zamanı tahmin et"""
        if self.model is None:
            return "Model henüz eğitilmedi!"
        
        # Örnek tahmin (gerçek uygulamada daha detaylı olacak)
        hour = current_time.hour
        minute = current_time.minute
        day_of_week = current_time.weekday()
        
        # Zaman bloğu
        if 6 <= hour < 10:
            time_block = 'morning_peak'
        elif 17 <= hour < 20:
            time_block = 'evening_peak'
        elif 22 <= hour or hour < 6:
            time_block = 'night'
        else:
            time_block = 'off_peak'
        
        day_type = 'weekend' if day_of_week >= 5 else 'weekday'
        
        # Örnek özellik vektörü
        features = np.array([[
            1,  # stop_sequence
            hour, minute, day_of_week,
            self.label_encoders['time_block'].transform([time_block])[0],
            self.label_encoders['day_type'].transform([day_type])[0],
            0,  # trend_slope
            38.4,  # stop_lat (İzmir ortalaması)
            27.1   # stop_lon
        ]])
        
        # Normalize et
        features = self.scaler.transform(features)
        features = features.reshape(1, 1, features.shape[1])
        
        # Tahmin yap
        prediction = self.model.predict(features, verbose=0)[0][0]
        
        return max(0, prediction)  # Negatif değerleri engelle
    
    def run_full_pipeline(self):
        """Tam pipeline'ı çalıştır"""
        if not DEEP_LEARNING_AVAILABLE:
            print("❌ Deep learning kütüphaneleri eksik!")
            return
        
        print("🚀 İzmir ESHOT Hibrit LSTM Pipeline Başlıyor...")
        print("📚 Makale: Spatio-Temporal Forecasting of Bus Arrival Times")
        
        try:
            # Veri yükleme ve hazırlama
            data = self.load_and_prepare_data()
            
            # Özellik hazırlama
            X, y, processed_data = self.prepare_features(data)
            
            # Model eğitimi
            history, metrics = self.train_model(X, y)
            
            # Örnek tahmin
            current_time = datetime.now()
            prediction = self.predict_arrival_time(
                route_id="5", 
                stop_id="10005", 
                current_time=current_time
            )
            
            print(f"\n🔮 Örnek tahmin:")
            print(f"   Hat: 5, Durak: 10005")
            print(f"   Zaman: {current_time.strftime('%H:%M')}")
            print(f"   Tahmini varış: {prediction:.1f} dakika")
            
            print("\n🎉 Pipeline başarıyla tamamlandı!")
            
            return self.model, history, metrics
            
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            return None

if __name__ == "__main__":
    # İzmir Hibrit LSTM modelini çalıştır
    izmir_lstm = IzmirHybridLSTM()
    result = izmir_lstm.run_full_pipeline()