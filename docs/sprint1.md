# 📅 Sprint 1 Guide: The Foundation
**Chủ đề:** Xây Dựng Hạ Tầng Container (Infrastructure Layer)
**Dự án:** Y.A.G.I (Yielding Adaptive Geo-spatial Intelligence)
**Trạng thái:** 🚀 Ready to Start

---

## 1. Mục Tiêu (Objectives)
Mục tiêu của Sprint này là xây dựng hạ tầng Big Data tối ưu cho việc tái hiện siêu bão Yagi.

*   ✅ **Services:** Spark (Master/Worker), Kafka (KRaft mode), MinIO, Portainer.
*   ✅ **Constraint:** Tổng lượng RAM tiêu thụ < 8GB.
*   ✅ **Outcome:** Lệnh `docker-compose up -d` kích hoạt thành công tất cả services.

---

## 2. Chuẩn Bị (Prerequisites)

### 2.1. Cấu Trúc Thư Mục
Hãy tổ chức lại folder dự án của bạn như sau:

```bash
Yagi/
├── data/               # Chứa dữ liệu thô (file csv Yagi)
├── docker-compose.yaml # File định nghĩa toàn bộ hạ tầng
├── jobs/               # Chứa code Spark Job (Ingestion, Processing)
├── notebooks/          # Chứa Jupyter Notebooks (Analysis/EDA)
├── schemas/            # Chứa định nghĩa Schema
└── services/           # Chứa code các microservices (Streamlit, API)
```

### 2.2. Copy Dữ Liệu
Hãy copy file `Hai phong, Viet Nam 2024-09-05 to 2024-09-09.csv` vào thư mục `data/` trong project.

---

## 3. Các Bước Thực Hiện (Implementation Steps)

### Bước 1: Tạo file `docker-compose.yaml`
Tạo file `docker-compose.yaml` tại thư mục gốc. Lưu ý bucket mặc định của MinIO là `yagi-data` và Kafka chạy mode KRaft.

```yaml
version: '3.8'

services:
  # --- Visualization & Monitoring ---
  portainer:
    image: portainer/portainer-ce:latest
    container_name: yagi_portainer
    ports:
      - "9000:9000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    restart: always

  # --- Message Queue (Kafka KRaft Mode - No Zookeeper) ---
  kafka:
    image: bitnami/kafka:latest
    container_name: yagi_kafka
    ports:
      - "9092:9092"
    environment:
      # KRaft settings
      - KAFKA_CFG_NODE_ID=0
      - KAFKA_CFG_PROCESS_ROLES=controller,broker
      - KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=0@kafka:9093
      # Listeners
      - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
      - KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      - KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER
    volumes:
      - kafka_data:/bitnami/kafka
    start_period: 30s
    restart: on-failure

  # --- Storage (MinIO - Data Lake) ---
  minio:
    image: minio/minio:latest
    container_name: yagi_minio
    ports:
      - "9000:9000" # API Port
      - "9001:9001" # Console Port
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=password123
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # --- Processing (Spark) ---
  spark-master:
    image: bitnami/spark:latest
    container_name: yagi_spark_master
    environment:
      - SPARK_MODE=master
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_RPC_ENCRYPTION_ENABLED=no
      - SPARK_LOCAL_STORAGE_ENCRYPTION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    ports:
      - "8080:8080"
      - "7077:7077"
    volumes:
      - ./jobs:/opt/bitnami/spark/jobs

  spark-worker:
    image: bitnami/spark:latest
    container_name: yagi_spark_worker
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=2G # Limit RAM
      - SPARK_WORKER_CORES=2
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    depends_on:
      - spark-master
    volumes:
      - ./jobs:/opt/bitnami/spark/jobs

  # --- Init Job (Optional: Create Bucket Automatically) ---
  # Bạn có thể dùng container 'mc' để tạo bucket tự động,
  # hoặc làm thủ công trong bước Smoke Test.

volumes:
  kafka_data:
  minio_data:
  portainer_data:
```

### Bước 2: Start Services
Chạy lệnh:
```bash
docker-compose up -d
```

### Bước 3: Smoke Test & Setup Bucket
1.  **Portainer (localhost:9000):** Kiểm tra xem cả 5 container (kafka, minio, spark-master, spark-worker, portainer) có xanh không.
2.  **MinIO (localhost:9001):**
    *   Login: `admin` / `password1234`.
    *   **QUAN TRỌNG:** Vào menu **Buckets** -> Create Bucket -> Đặt tên: `yagi-data` (Đây là nơi chứa dữ liệu bão).
3.  **Spark (localhost:8080):** Đảm bảo Worker đang Alive.

### Bước 4: Validation
Docker Cluster của bạn đã sẵn sàng tiếp nhận dữ liệu báo bão trong Sprint 2!
