import json
import time
import joblib
import numpy as np
from kafka import KafkaConsumer, KafkaProducer

# Cấu hình
KAFKA_BOOTSTRAP_SERVERS = "yagi-kafka:9092"
INPUT_TOPIC = "weather-stream"
ALERT_TOPIC = "storm-alerts"
MODEL_PATH = "/app/storm_classifier.pkl"

# Ngưỡng cảnh báo
WIND_THRESHOLD = 60  # km/h

def load_model():
    """Load trained model"""
    try:
        model = joblib.load(MODEL_PATH)
        print(f"✅ Model loaded from {MODEL_PATH}")
        return model
    except FileNotFoundError:
        print(f"⚠️ Model not found at {MODEL_PATH}, using rule-based prediction")
        return None

def create_alert(record, prediction, confidence=None):
    """Tạo message cảnh báo"""
    alert_level = "🔴 CRITICAL" if prediction == 1 else "🟢 SAFE"
    
    alert = {
        "timestamp": record.get("datetime", time.strftime("%Y-%m-%d %H:%M:%S")),
        "alert_level": alert_level,
        "is_dangerous": bool(prediction),
        "windspeed": record.get("windspeed", 0),
        "sealevelpressure": record.get("sealevelpressure", 0),
        "humidity": record.get("humidity", 0),
        "message": f"Wind speed: {record.get('windspeed', 0)} km/h"
    }
    
    if confidence is not None:
        alert["confidence"] = f"{confidence:.2%}"
    
    return alert

def rule_based_predict(record):
    """Fallback: Rule-based prediction nếu không có model"""
    wind = record.get("windspeed", 0) or 0
    pressure = record.get("sealevelpressure", 1013) or 1013
    
    # Gió > 60km/h HOẶC áp suất < 990mb = Nguy hiểm
    if wind > WIND_THRESHOLD or pressure < 990:
        return 1
    return 0

def main():
    print("🚀 Storm Predictor Service Starting...")
    
    # Load model
    model = load_model()
    
    # Kafka Consumer
    consumer = KafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        group_id='predictor-group'
    )
    
    # Kafka Producer (for alerts)
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    print(f"📡 Listening to topic: {INPUT_TOPIC}")
    print(f"📢 Alerts will be sent to: {ALERT_TOPIC}")
    
    for message in consumer:
        record = message.value
        
        try:
            if model is not None:
                # ML-based prediction (dùng đúng tên cột từ CSV)
                features = np.array([[
                    record.get('temp', 0) or 0,
                    record.get('sealevelpressure', 1013) or 1013,
                    record.get('humidity', 50) or 50,
                    record.get('cloudcover', 0) or 0,
                    record.get('precip', 0) or 0,
                    record.get('windgust', 0) or 0
                ]])
                prediction = model.predict(features)[0]
                proba = model.predict_proba(features)[0]
                confidence = max(proba)
            else:
                # Rule-based fallback
                prediction = rule_based_predict(record)
                confidence = None
            
            # Tạo và gửi alert
            alert = create_alert(record, prediction, confidence)
            producer.send(ALERT_TOPIC, alert)
            
            # Log
            status = "⚠️ DANGEROUS" if prediction == 1 else "✅ Safe"
            print(f"{record.get('datetime')} | Wind: {record.get('windspeed', 0):>6} km/h | {status}")
            
        except Exception as e:
            print(f"❌ Error processing: {e}")
            continue
    
    consumer.close()
    producer.close()

if __name__ == "__main__":
    main()