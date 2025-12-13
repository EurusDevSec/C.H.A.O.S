
# ĐỀ CƯƠNG BÁO CÁO ĐỒ ÁN BIG DATA
**Đề tài:** Xây dựng Hệ thống Data Lakehouse & MLOps Cảnh báo Thiên tai Thời gian thực
**(Case Study: Tái hiện Siêu bão Yagi 2024)**

---

### PHẦN MỞ ĐẦU

**1. Lý do chọn đề tài**
* **Tính cấp thiết:** Thiên tai (Bão Yagi tháng 9/2024) gây thiệt hại lớn về người và của. Nhu cầu cần hệ thống cảnh báo sớm dựa trên dữ liệu thời gian thực.
* **Hạn chế của hệ thống cũ:** Các hệ thống phân tích truyền thống (Batch processing) có độ trễ cao, không xử lý kịp tốc độ dữ liệu từ cảm biến IoT.
* **Giải pháp:** Ứng dụng Big Data (Lambda Architecture) để vừa xử lý nóng (Real-time), vừa lưu trữ lịch sử (Batch) phục vụ AI.

**2. Mục tiêu đề tài**
* Xây dựng pipeline xử lý dữ liệu Streaming End-to-End.
* Triển khai kiến trúc **Data Lakehouse** (MinIO + Delta Lake).
* Ứng dụng **MLOps** để dự báo khí tượng.
* Tái hiện (Data Replay) dữ liệu thực tế của bão Yagi tại Hải Phòng/Quảng Ninh.

**3. Phạm vi nghiên cứu**
* **Dữ liệu:** Dữ liệu khí tượng lịch sử (Gió, Áp suất, Mưa) giai đoạn bão Yagi (09/2024).
* **Công nghệ:** Apache Kafka, Spark Streaming, MinIO, Docker.

---

### CHƯƠNG 1: CƠ SỞ LÝ THUYẾT (THEORETICAL BACKGROUND)

**1.1. Tổng quan về Big Data**
* Định nghĩa 3V (Volume, Velocity, Variety).
* Các thách thức trong xử lý dữ liệu luồng (Stream Processing).

**1.2. Các kiến trúc Big Data hiện đại**
* **Lambda Architecture:** Phân tích sâu về Speed Layer (Xử lý nóng) và Batch Layer (Xử lý lạnh).
* **Data Lakehouse:** Sự kết hợp giữa Data Lake (MinIO) và Data Warehouse (Delta Lake - ACID, Schema Enforcement).

**1.3. Công nghệ sử dụng (Tech Stack)**
* **Apache Kafka (KRaft Mode):** Cơ chế Pub/Sub, Decoupling hệ thống.
* **Apache Spark:** Mô hình Master-Worker, Spark Streaming vs Spark SQL.
* **Containerization (Docker):** Quản lý hạ tầng Microservices.
* **MLOps:** Quy trình huấn luyện và triển khai model dự báo.

---

### CHƯƠNG 2: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG (SYSTEM DESIGN)

**2.1. Kiến trúc tổng thể (Architecture)**
* *Sơ đồ kiến trúc Project Yagi* 
![alt text](image.png)
* Giải thích luồng dữ liệu (Data Flow):
    1.  **Ingestion:** Python Producer giả lập cảm biến.
    2.  **Message Queue:** Kafka buffer dữ liệu.
    3.  **Processing:** Spark Streaming xử lý, tính toán cửa sổ trượt (Windowing).
    4.  **Storage:** Ghi xuống MinIO dưới dạng Delta Lake (Parquet).
    5.  **Serving:** Streamlit Dashboard & Telegram Alert.

**2.2. Thiết kế dữ liệu**
* **Nguồn dữ liệu:** Mô tả cấu trúc file CSV bão Yagi (Time, Wind Speed, Pressure...).
* **Lược đồ (Schema):** Cấu trúc bảng Delta Lake (Parquet) lưu trong MinIO.

**2.3. Thiết kế kịch bản kiểm thử (Chaos Engineering)**
* Kịch bản 1: Hệ thống chịu tải cao khi bão đổ bộ (Tăng tốc độ gửi tin).
* Kịch bản 2: Tự phục hồi khi một Node (Spark Worker) bị sập.

---

### CHƯƠNG 3: TRIỂN KHAI VÀ XÂY DỰNG (IMPLEMENTATION)

**3.1. Chuẩn bị môi trường**
* Cấu hình Docker Compose (Kafka, Spark, MinIO, Portainer).
* Tối ưu hóa tài nguyên cho máy 16GB RAM (Spark Worker limit 2GB).

**3.2. Xây dựng Ingestion Layer (Sprint 2)**
* Thuật toán **Data Replay**: Cách Producer đọc CSV và bắn message vào Kafka theo thời gian thực.
* Code minh họa: `producer.py`.

**3.3. Xây dựng Processing & Storage Layer (Sprint 3)**
* Xử lý Spark Streaming: Đọc từ Kafka, làm sạch dữ liệu.
* Lưu trữ: Ghi dữ liệu vào MinIO với định dạng Delta Lake.
* **MLOps:** Quy trình train model trên Google Colab và đóng gói vào Docker để dự báo.

**3.4. Xây dựng Serving Layer (Sprint 4)**
* Dashboard Streamlit: Hiển thị biểu đồ gió, áp suất realtime.
* Hệ thống cảnh báo: Logic kích hoạt gửi tin nhắn Telegram khi gió > cấp 12.

---

### CHƯƠNG 4: KẾT QUẢ THỰC NGHIỆM (RESULTS & EVALUATION)

**4.1. Kịch bản Demo: Tái hiện Bão Yagi**
* Mô tả quá trình chạy hệ thống với dữ liệu ngày 07/09/2024.
* **Kết quả hiển thị:** Screenshot Dashboard khi gió tăng vọt, tin nhắn cảnh báo trên điện thoại.

**4.2. Đánh giá hiệu năng**
* **Latency (Độ trễ):** Thời gian từ lúc Producer gửi đến lúc Dashboard hiện thị (Ví dụ: < 1 giây).
* **Throughput:** Khả năng xử lý số lượng message/giây.
* **Reliability:** Hệ thống vẫn chạy tốt khi tắt nóng 1 container (Chaos Test).

**4.3. So sánh với lý thuyết**
* Chứng minh hệ thống đáp ứng đúng nguyên lý Lambda Architecture và Data Lakehouse.

---

### KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

**1. Kết luận**
* Đã xây dựng thành công hệ thống Yagi.
* Làm chủ các công nghệ Big Data cốt lõi.
* Chứng minh tính khả thi của việc phân tích dữ liệu bão thời gian thực.

**2. Hạn chế**
* Dữ liệu đầu vào mới chỉ là mô phỏng (Simulation) từ file CSV, chưa kết nối cảm biến vật lý thật.
* Hạ tầng chạy trên 1 máy Local (Docker), chưa triển khai Cluster thực tế trên Cloud (AWS/GCP).

**3. Hướng phát triển**
* Triển khai lên Cloud (Kubernetes).
* Tích hợp thêm dữ liệu ảnh vệ tinh/Radar.

---

### TÀI LIỆU THAM KHẢO
1.  Documentation: Apache Kafka, Apache Spark, Delta Lake.
2.  Dữ liệu bão Yagi: Visual Crossing Weather Data.
3.  Các bài báo về Lambda Architecture.

---

