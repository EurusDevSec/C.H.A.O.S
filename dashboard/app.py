import streamlit as st
import pandas as pd
import json
from kafka import KafkaConsumer
import time
from datetime import datetime

# Cấu hình trang
st.set_page_config(
    page_title="YAGI Storm Monitor",
    page_icon="🌪️",
    layout="wide"
)

# Tiêu đề
st.title("🌪️ YAGI Storm Real-time Monitor")
st.markdown("Hệ thống giám sát và cảnh báo bão thời gian thực")

# Cấu hình Kafka
KAFKA_BOOTSTRAP_SERVERS = 'yagi-kafka:9092'
TOPIC_WEATHER = 'weather-stream'
TOPIC_ALERTS = 'storm-alerts'

# Hàm nhận dữ liệu từ Kafka (giả lập polling để không block UI)
# Lưu ý: Streamlit hoạt động theo cơ chế rerun, nên việc tích hợp Kafka consumer trực tiếp
# cần khéo léo. Ở đây ta dùng placeholder để update.

# Tạo các placeholder cho UI
col1, col2, col3 = st.columns(3)
with col1:
    metric_wind = st.empty()
with col2:
    metric_pressure = st.empty()
with col3:
    metric_status = st.empty()

st.divider()

col_chart_1, col_chart_2 = st.columns(2)
with col_chart_1:
    st.subheader("Tốc độ gió (km/h)")
    chart_wind = st.line_chart(x=None, y=None, height=300)

with col_chart_2:
    st.subheader("Áp suất khí quyển (mb)")
    chart_pressure = st.line_chart(x=None, y=None, height=300)

st.subheader("🚨 Nhật ký Cảnh báo")
alert_log = st.empty()

# Khởi tạo session state để lưu dữ liệu
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=['timestamp', 'windspeed', 'pressure'])
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

def consume_data():
    consumer = KafkaConsumer(
        TOPIC_WEATHER,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest', # Chỉ đọc dữ liệu mới nhất
        group_id='dashboard-group-v1',
        consumer_timeout_ms=100 # Không chờ quá lâu
    )

    # Lấy dữ liệu mới
    new_rows = []
    for message in consumer:
        record = message.value
        timestamp = record.get('datetime')
        wind = record.get('windspeed', 0)
        pressure = record.get('sealevelpressure', 0)

        new_rows.append({
            'timestamp': timestamp,
            'windspeed': wind,
            'pressure': pressure
        })

        # Update Metrics ngay lập tức
        metric_wind.metric("Gió", f"{wind} km/h", delta_color="inverse")
        metric_pressure.metric("Áp suất", f"{pressure} mb")

        if wind > 60:
            metric_status.error("⚠️ NGUY HIỂM")
        else:
            metric_status.success("✅ AN TOÀN")

    # Cập nhật DataFrame
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        st.session_state.data = pd.concat([st.session_state.data, new_df], ignore_index=True).tail(100) # Giữ 100 điểm dữ liệu cuối

        # Vẽ lại biểu đồ
        chart_wind.line_chart(st.session_state.data.set_index('timestamp')['windspeed'])
        chart_pressure.line_chart(st.session_state.data.set_index('timestamp')['pressure'])

# Nút để chạy (Streamlit tự động rerun nhưng ta cần vòng lặp cho Kafka)
if st.button('Bắt đầu giám sát'):
    st.success("Đang kết nối Kafka...")
    while True:
        consume_data()
        time.sleep(1)