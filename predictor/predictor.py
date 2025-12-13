import json
import time
import joblib
import numpy as np
from kafka import KafkaConsumer, KafkaProducer, TopicPartition

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
    print("🚀 Storm Predictor Service Starting...", flush=True)
    
    # Load model
    model = load_model()
    
    # Kafka Consumer
    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                group_id='predictor-group-v6'
            )
            print("✅ Connected to Kafka Consumer", flush=True)
        except Exception as e:
            print(f"⚠️ Failed to connect to Kafka Consumer: {e}. Retrying in 5s...", flush=True)
            time.sleep(5)
    
    # Kafka Producer (for alerts)
    producer = None
    while producer is None:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("✅ Connected to Kafka Producer", flush=True)
        except Exception as e:
            print(f"⚠️ Failed to connect to Kafka Producer: {e}. Retrying in 5s...", flush=True)
            time.sleep(5)
    
    print(f"📡 Listening to topic: {INPUT_TOPIC}", flush=True)
    
    # Debug: Check topics
    try:
        topics = consumer.topics()
        print(f"📋 Available topics: {topics}", flush=True)
        if INPUT_TOPIC not in topics:
            print(f"⚠️ Warning: Topic '{INPUT_TOPIC}' not found in available topics!", flush=True)
    except Exception as e:
        print(f"⚠️ Error fetching topics: {e}", flush=True)

    print(f"📢 Alerts will be sent to: {ALERT_TOPIC}", flush=True)
    
    # Manual Partition Assignment (Bypass Group Rebalance issues)
    partitions = None
    while not partitions:
        partitions = consumer.partitions_for_topic(INPUT_TOPIC)
        if not partitions:
            print(f"⏳ Waiting for partitions for topic {INPUT_TOPIC}...", flush=True)
            time.sleep(2)
    
    topic_partitions = [TopicPartition(INPUT_TOPIC, p) for p in partitions]
    consumer.assign(topic_partitions)
    print(f"✅ Manually assigned to partitions: {topic_partitions}", flush=True)
    
    # Debug: Check offsets
    try:
        beginning_offsets = consumer.beginning_offsets(topic_partitions)
        end_offsets = consumer.end_offsets(topic_partitions)
        print(f"📊 Topic Offsets - Beginning: {beginning_offsets}, End: {end_offsets}", flush=True)
    except Exception as e:
        print(f"⚠️ Error checking offsets: {e}", flush=True)

    # Force read from beginning
    consumer.seek_to_beginning()
    
    # Poll loop
    try:
        while True:
            # Poll for messages
            msg_pack = consumer.poll(timeout_ms=1000)
            
            if not msg_pack:
                continue
            
            for tp, messages in msg_pack.items():
                for message in messages:
                    print(f"📥 Received message: {message.value.get('datetime')}", flush=True)
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
                        print(f"{record.get('datetime')} | Wind: {record.get('windspeed', 0):>6} km/h | {status}", flush=True)
                        
                    except Exception as e:
                        print(f"❌ Error processing: {e}", flush=True)
                        continue

    except KeyboardInterrupt:
        print("🛑 Stopping...", flush=True)
    finally:
        consumer.close()
        producer.close()

if __name__ == "__main__":
    main()