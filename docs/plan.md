# 🌪️ PROJECT Y.A.G.I
**(Yielding Adaptive Geo-spatial Intelligence)**

> *"From the Storm that broke us, comes the Intelligence that saves us."*
> *(Từ cơn bão tàn phá, sinh ra trí tuệ bảo vệ chúng ta.)*

---

### 1. TỔNG QUAN DỰ ÁN (Project Overview)

* **Tên đề tài báo cáo:** Xây dựng Hệ thống Data Lakehouse & MLOps End-to-End cho Cảnh báo Thiên tai Thời gian thực (Case Study: Siêu bão Yagi 2024).
* **Mục tiêu cốt lõi:** Tái hiện lại cơn bão lịch sử Yagi dưới dạng dữ liệu luồng (Streaming), qua đó chứng minh khả năng xử lý, lưu trữ và cảnh báo sớm của hệ thống Big Data hiện đại.
* **Công nghệ định hướng:** Lambda Architecture, Data Lakehouse, MLOps, Containerization.

---

### 2. KIẾN TRÚC KỸ THUẬT (Technical Architecture)

Hệ thống được thiết kế theo mô hình **Lambda Architecture** tối ưu cho máy cấu hình 16GB RAM:

#### 🟢 Layer 1: Ingestion (Thu thập & Giả lập)
* **Data Source:** File `res/Hai phong, Viet Nam 2024-09-05 to 2024-09-09.csv`.
* **Technique:** **Data Replay**. Script Python đọc file CSV theo từng dòng, đẩy vào hệ thống với tốc độ thực (hoặc x10 tốc độ) để giả lập cảm biến IoT đang gửi dữ liệu bão về.
* **Message Queue:** **Apache Kafka (KRaft Mode)**. Loại bỏ Zookeeper để tiết kiệm RAM. Đóng vai trò vùng đệm (Buffer) chịu tải cao.

#### 🔵 Layer 2: Speed Layer (Xử lý Nóng - Real-time)
* **Engine:** **Apache Spark Streaming**.
* **Luồng xử lý:** Đọc từ Kafka -> Xử lý/Làm sạch -> Đẩy thẳng sang **Prediction Service**.
* **Nhiệm vụ:** Phát hiện ngay lập tức các chỉ số nguy hiểm (Gió > 100km/h, Áp suất tụt giảm).

#### 🟣 Layer 3: Batch/Serving Layer (Lưu trữ & MLOps)
* **Data Lakehouse:** **MinIO (S3)** + **Delta Lake**.
    * Lưu trữ dữ liệu lịch sử bão Yagi bền vững (ACID Transactions).
    * Phục vụ truy vấn lịch sử (Time Travel).
* **MLOps Training:** **Google Colab**.
    * Lấy dữ liệu từ Lakehouse -> Train model dự báo bão -> Đóng gói Model.
* **Inference:** **Docker Container** chạy model đã train, nhận dữ liệu nóng từ Kafka để đưa ra cảnh báo.

#### 🟠 Layer 4: Visualization (Hiển thị)
* **Dashboard:** **Streamlit**. Vẽ biểu đồ diễn biến bão Real-time.
* **Alert:** **Telegram Bot**. Bắn tin nhắn cảnh báo khẩn cấp tới điện thoại.

---

### 3. KẾ HOẠCH THỰC HIỆN (4-Week Agile Sprint)

#### 📅 Sprint 1: The Foundation - Hạ Tầng Container
* **Mục tiêu:** Dựng cụm Cluster ảo. Lệnh `docker-compose up` chạy mượt, Kafka và MinIO xanh đèn.
* **Công việc:**
    1.  Cài đặt Docker Desktop.
    2.  Thiết lập môi trường:
        * Tạo cấu trúc thư mục.
        * Cấu hình Git.
    3.  Viết `docker-compose.yaml`:
        * `portainer`: Monitoring & Container Management.
        * `kafka`: Image `apache/kafka`, KRaft mode (No Zookeeper).
        * `minio`: Image `minio/minio`, tạo bucket `yagi-data`.
        * `spark-master` & `spark-worker`: Image `apache/spark`, giới hạn RAM Worker 2GB.
    4.  Kiểm tra kết nối các service (Smoke Test).

#### 📅 Sprint 2: The Storm Replay - Dòng Chảy Dữ Liệu
* **Mục tiêu:** Tái hiện cơn bão Yagi trên hệ thống. Dữ liệu từ CSV chảy vào Kafka và nằm an toàn trong Delta Lake.
* **Công việc:**
    1.  Xử lý file CSV `Hai phong_Yagi.csv`: Làm sạch, chuẩn hóa timestamp.
    2.  Code `yagi_producer.py`: Đọc CSV, giả lập delay, bắn vào Kafka topic `weather-stream`.
    3.  Code `spark_ingestion.py`:
        * Đọc Kafka topic `weather-stream`.
        * Ghi xuống MinIO bucket `yagi-data` định dạng **Delta Lake**.
    4.  Kiểm tra: Thấy file Parquet xuất hiện liên tục trong MinIO console.

#### 📅 Sprint 3: The Intelligence - MLOps Logic
* **Mục tiêu:** Hệ thống có "não". Dự báo được xu hướng bão.
* **Công việc:**
    1.  Train Model (Colab):
        * Sử dụng dữ liệu Yagi (hoặc dữ liệu lịch sử tương tự).
        * Train model `StormPrediction` (Regression dự báo sức gió hoặc Classification rủi ro).
    2.  Export Model: Lưu model dạng `.zip` hoặc `.pkl`.
    3.  Deploy (Local): Viết service `predictor` trong Docker.
        * Subscribe Kafka `weather-stream`.
        * Predict: Nếu gió > 60km/h -> Gửi cảnh báo vào Kafka topic `alerts`.

#### 📅 Sprint 4: The Interface & Resilience - Giao Diện & Chịu Lỗi
* **Mục tiêu:** Dashboard đẹp, Demo khả năng tự phục hồi.
* **Công việc:**
    1.  Code Dashboard Streamlit:
        * Chart 1: Tốc độ gió thực tế (Real-time).
        * Chart 2: Áp suất khí quyển.
        * Vùng cảnh báo đỏ khi bão về.
    2.  Tích hợp Telegram API báo tin.
    3.  **Chaos Engineering Test:**
        * Kịch bản: Đang bão to -> Tắt container `predictor` -> Hệ thống tự restart container -> Dashboard tiếp tục chạy, không mất dữ liệu.

---

### 4. TECH STACK (Tối ưu 16GB RAM)

| Thành phần | Công nghệ | Ghi chú |
| :--- | :--- | :--- |
| **Ngôn ngữ** | Python 3.9+ | PySpark, Streamlit, Pandas |
| **Message Queue** | **Apache Kafka** | **KRaft Mode** (No Zookeeper - Tiết kiệm RAM) |
| **Big Data Engine** | **Apache Spark** | Streaming & SQL |
| **Storage** | **MinIO** | S3 Compatible |
| **Data Format** | **Delta Lake** | ACID, Time Travel |
| **DevOps** | Docker Compose | Quản lý hạ tầng |
| **Monitoring** | **Portainer** | Quản lý container trực quan |
| **Training** | Google Colab | Tận dụng Cloud GPU |
