# 📅 Sprint 1 Guide: The Foundation
**Chủ đề:** Xây Dựng Hạ Tầng Container (Infrastructure Layer)
**Trạng thái:** 🚀 Ready to Start

---

## 1. Mục Tiêu (Objectives)
Mục tiêu của Sprint này là xây dựng "bộ khung" vững chắc cho dự án C.H.A.O.S. Kết thúc Sprint 1, bạn cần có một cụm Cluster chạy trên Local (Docker) mượt mà, không ngốn quá nhiều RAM.

*   ✅ **Services:** Spark (Master/Worker), Kafka (KRaft mode), MinIO, Portainer.
*   ✅ **Constraint:** Tổng lượng RAM tiêu thụ < 8GB (để chừa chỗ cho OS và trình duyệt).
*   ✅ **Outcome:** Lệnh `docker-compose up -d` kích hoạt thành công tất cả services.

---

## 2. Chuẩn Bị (Prerequisites)

### 2.1. Cấu Trúc Thư Mục
Tạo cấu trúc thư mục dự án như sau:

```bash
C.H.A.O.S/
├── data/               # Chứa dữ liệu thô (nếu tải về local)
├── docker-compose.yaml # File định nghĩa toàn bộ hạ tầng
├── jobs/               # Chứa code Spark Job (Ingestion, Processing)
├── notebooks/          # Chứa Jupyter Notebooks (Analysis/EDA)
├── schemas/            # Chứa định nghĩa Schema (nếu cần)
└── services/           # Chứa code các microservices (API, Dashboard)
```

### 2.2. Công Cụ
*   Docker Desktop (đã bật Kubernetes hoặc không, tùy chọn - khuyến khích tắt K8s để nhẹ máy).
*   VS Code.

---

## 3. Các Bước Thực Hiện (Implementation Steps)

### Bước 1: Tạo file `docker-compose.yaml`
Đây là bước quan trọng nhất. Hãy tạo file `docker-compose.yaml` tại thư mục gốc với nội dung tham khảo sau (đã tối ưu KRaft và Portainer):

```yaml
version: '3.8'

services:
  # --- Visualization & Monitoring ---
  portainer:
    image: portainer/portainer-ce:latest
    container_name: chaos_portainer
    ports:
      - "9000:9000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    restart: always

  # --- Message Queue (Kafka KRaft Mode - No Zookeeper) ---
  kafka:
    image: bitnami/kafka:latest
    container_name: chaos_kafka
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
    start_period: 30s  # Đợi ổn định
    restart: on-failure

  # --- Storage (MinIO - Data Lake) ---
  minio:
    image: minio/minio:latest
    container_name: chaos_minio
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
    container_name: chaos_spark_master
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
      - ./jobs:/opt/bitnami/spark/jobs # Mount code vào container

  spark-worker:
    image: bitnami/spark:latest
    container_name: chaos_spark_worker
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=2G # Giới hạn RAM Worker
      - SPARK_WORKER_CORES=2
      - SPARK_RPC_AUTHENTICATION_ENABLED=no
      - SPARK_SSL_ENABLED=no
    depends_on:
      - spark-master
    volumes:
      - ./jobs:/opt/bitnami/spark/jobs

volumes:
  kafka_data:
  minio_data:
  portainer_data:
```

### Bước 2: Start Services & Kiểm Tra Lần Đầu
Mở terminal tại thư mục dự án và chạy:

```bash
docker-compose up -d
```

⏳ **Chờ khoảng 1-2 phút** để các service khởi động hoàn toàn.

### Bước 3: Smoke Test (Kiểm tra sống còn)
Truy cập các địa chỉ sau trên trình duyệt để đảm bảo mọi thứ đã "lên đèn":

1.  **Portainer (Quản lý Container):**
    *   URL: `http://localhost:9000`
    *   Hành động: Tạo tài khoản admin lần đầu. Chọn môi trường "Local". Kiểm tra xem có 5 container đang chạy (green state) không.
2.  **MinIO (Data Lake):**
    *   URL: `http://localhost:9001`
    *   Login: `admin` / `password123`.
    *   Hành động: Thử tạo một Bucket tên là `climate-data`.
3.  **Spark Master:**
    *   URL: `http://localhost:8080`
    *   Hành động: Kiểm tra xem có 1 Worker đang status `ALIVE` không.

### Bước 4: Clean Up (Optional)
Nếu muốn tắt hệ thống để nghỉ ngơi:
```bash
docker-compose down
# Hoặc gỡ bỏ cả volumes (xóa sạch dữ liệu)
docker-compose down -v
```

---

## 4. Troubleshooting (Gỡ Rối)

*   **Lỗi: Port already in use**:
    *   Nguyên nhân: Có service khác (như IIS, Skype, hoặc project cũ) đang chiếm port 8080 hoặc 9000.
    *   Khắc phục: Đổi port mapping trong `docker-compose.yaml`. Ví dụ đổi Spark UI thành `8081:8080`.
*   **Lỗi: Kafka Crashed (Exited 1)**:
    *   Nguyên nhân: Thường do thiếu ID node.
    *   Khắc phục: Đảm bảo biến `KAFKA_CFG_NODE_ID` đã được set. Nếu vẫn lỗi, thử xóa volume `docker-compose down -v` và chạy lại.
*   **Máy quá lag**:
    *   Khắc phục: Giảm `SPARK_WORKER_MEMORY` xuống `1G` hoặc tắt bớt trình duyệt Chrome.

---

🚀 **Chúc bạn hoàn thành Sprint 1 tốt đẹp!**
