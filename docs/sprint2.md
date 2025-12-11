# 📅 Sprint 2 Guide: The Storm Replay (Dòng Chảy Dữ Liệu)
**Mục tiêu:** Tái hiện cơn bão Yagi bằng cách đẩy dữ liệu từ CSV vào Kafka và lưu trữ xuống Data Lake (MinIO) thông qua Spark Streaming.

---

## 1. Cập nhật Hạ Tầng (Networking Fix)
Để Producer (chạy ở Local) và Spark (chạy trong Docker) đều kết nối được với Kafka, ta cần mở thêm cổng kết nối.

### Bước 1.1: Sửa file `docker-compose.yaml`
Cập nhật service `kafka` như sau:

```yaml
  kafka:
    image: apache/kafka:latest
    container_name: yagi_kafka
    ports:
      - "9092:9092" # Internal (Spark -> Kafka) - Thực ra port này dùng trong Docker network
      - "9094:9094" # External (Local Producer -> Kafka) - MỚI
    environment:
      - KAFKA_NODE_ID=0
      - KAFKA_PROCESS_ROLES=controller,broker
      - KAFKA_CONTROLLER_QUORUM_VOTERS=0@yagi_kafka:9093
      - KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093,EXTERNAL://:9094
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://yagi_kafka:9092,EXTERNAL://localhost:9094
      - KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT
      - KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER
      - KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT
    volumes:
      - kafka_data:/var/lib/kafka/data
    restart: on-failure
```

*Giải thích:*
*   `PLAINTEXT (9092)`: Dành cho các container bên trong (Spark) gọi tới `yagi_kafka:9092`.
*   `EXTERNAL (9094)`: Dành cho máy tính của bạn (Producer) gọi tới `localhost:9094`.

### Bước 1.2: Apply thay đổi
```bash
docker-compose up -d
```

---

## 2. Chuẩn Bị Môi Trường Python (Local)
Cài đặt các thư viện cần thiết để chạy Producer trên máy của bạn:

```bash
pip install pandas kafka-python
```

---

## 3. Implement Producer (Python)
Tạo file `jobs/yagi_producer.py`. Script này đọc file CSV và bắn vào Kafka từng dòng một.

**Lưu ý:** Đổi tên file dữ liệu trong thư mục `data/` thành `yagi_storm.csv` cho dễ gọi, hoặc sửa đường dẫn trong code.

```python
import time
import json
import pandas as pd
from kafka import KafkaProducer

# Cấu hình
KAFKA_TOPIC = "weather-stream"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9094" # Port External
DATA_PATH = "../data/yagi_storm.csv" # Đường dẫn tới file CSV
SPEED_FACTOR = 1 # 1 = Real-time, 10 = Nhanh gấp 10 lần

def json_serializer(data):
    return json.dumps(data).encode("utf-8")

def run_producer():
    # 1. Khởi tạo Producer
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
        value_serializer=json_serializer
    )
    
    # 2. Đọc dữ liệu
    print(f"Reading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    # Lọc các cột cần thiết nếu cần (datetime, wind_kph, pressure_mb, ...)
    # df = df[['datetime', 'wind_kph', 'pressure_mb', 'precip_mm', 'humidity']]
    
    print(f"Start sending {len(df)} records to Kafka topic '{KAFKA_TOPIC}'...")
    
    for index, row in df.iterrows():
        record = row.to_dict()
        
        # Gửi tin nhắn
        producer.send(KAFKA_TOPIC, record)
        print(f"Sent: {record['datetime']} - Wind: {record.get('wind_kph', 0)} km/h")
        
        # Giả lập delay (nếu cần chính xác theo timestamp thì code phức tạp hơn, ở đây ta sleep tượng trưng)
        time.sleep(1 / SPEED_FACTOR)
        
    producer.flush()
    print("Done!")

if __name__ == "__main__":
    run_producer()
```

---

## 4. Implement Spark Job (Ingestion)
Tạo file `jobs/spark_ingestion.py`. Đây là trái tim của Pipeline, chạy bên trong container Spark.

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# Cấu hình MinIO & Kafka
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
MINIO_ENDPOINT = "http://yagi_minio:9000"
KAFKA_BOOTSTRAP_SERVERS = "yagi_kafka:9092" # Port Internal
TOPIC = "weather-stream"

def main():
    # 1. Khởi tạo Spark Session với Delta & S3 Support
    spark = SparkSession.builder \
        .appName("YagiStormIngestion") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT) \
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # 2. Định nghĩa Schema (Điều chỉnh theo cột trong CSV của bạn)
    schema = StructType([
        StructField("datetime", StringType(), True),
        StructField("temp_c", DoubleType(), True),
        StructField("wind_kph", DoubleType(), True),
        StructField("pressure_mb", DoubleType(), True),
        StructField("precip_mm", DoubleType(), True),
        StructField("humidity", DoubleType(), True),
        StructField("cloud", DoubleType(), True),
        StructField("condition_text", StringType(), True)
    ])

    # 3. Đọc dữ liệu từ Kafka
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", TOPIC) \
        .option("startingOffsets", "earliest") \
        .load()

    # 4. Parse JSON
    parsed_df = kafka_df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    # 5. Ghi dữ liệu xuống MinIO (Delta Lake)
    query = parsed_df.writeStream \
        .format("delta") \
        .outputMode("append") \
        .option("checkpointLocation", "s3a://yagi-data/checkpoints/weather") \
        .option("path", "s3a://yagi-data/bronze/weather") \
        .start()

    print("Spark Streaming is running... Data is flowing to MinIO.")
    query.awaitTermination()

if __name__ == "__main__":
    main()
```

---

## 5. Thực Thi Pipeline

### Bước 5.1: Submit Job Spark (Trong Container)
Mở một terminal mới (Git Bash hoặc CMD), chạy lệnh sau để đưa Job vào Spark Master:

```bash
docker exec -it yagi_spark_master //opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.jars.ivy=//tmp/.ivy \
  --conf spark.hadoop.fs.s3a.endpoint=http://yagi_minio:9000 \
  --conf spark.hadoop.fs.s3a.access.key=admin \
  --conf spark.hadoop.fs.s3a.secret.key=password123 \
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
  --conf spark.hadoop.fs.s3a.path.style.access=true \
  --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,io.delta:delta-spark_2.12:3.1.0,org.apache.hadoop:hadoop-aws:3.3.4 \
  //opt/spark/jobs/spark_ingestion.py
```
*(Lưu ý: Trên Windows Git Bash, ta cần dùng dấu `//` ở đầu đường dẫn để tránh lỗi tự động chuyển đổi đường dẫn).*

### Bước 5.2: Chạy Producer (Trên Local)
Mở một terminal khác (tại folder dự án), chạy file Python để bắt đầu bắn dữ liệu:

```bash
cd jobs
python yagi_producer.py
```

### Bước 5.3: Kiểm Tra Kết Quả
1.  Nhìn vào log của Producer, bạn sẽ thấy nó đang gửi từng dòng `Sent: ...`.
2.  Mở trình duyệt vào MinIO `localhost:9001` (login `admin` / `password123`).
3.  Vào bucket `yagi-data`, kiểm tra folder `bronze/weather`. Nếu thấy các file `.parquet` xuất hiện là thành công! 🎉
