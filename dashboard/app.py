import streamlit as st
import pandas as pd
import json
from kafka import KafkaConsumer
import time

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
    chart_wind_placeholder = st.empty()

with col_chart_2:
    st.subheader("Áp suất khí quyển (mb)")
    chart_pressure_placeholder = st.empty()

st.subheader("🚨 Nhật ký Cảnh báo")
alert_log = st.empty()

# Khởi tạo session state
if 'data' not in st.session_state:
    # Khởi tạo DataFrame với đúng kiểu dữ liệu để tránh warning
    st.session_state.data = pd.DataFrame({
        'timestamp': pd.Series(dtype='str'),
        'windspeed': pd.Series(dtype='float'),
        'pressure': pd.Series(dtype='float')
    })

def init_consumer():
    try:
        consumer = KafkaConsumer(
            TOPIC_WEATHER,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='dashboard-group-v2', # Đổi group ID mới
            consumer_timeout_ms=1000
        )
        return consumer
    except Exception as e:
        st.error(f"Không thể kết nối Kafka: {e}")
        return None

# Nút để chạy
if st.button('Bắt đầu giám sát'):
    consumer = init_consumer()
    
    if consumer:
        st.success("Đã kết nối Kafka! Đang chờ dữ liệu...")
        
        # Vòng lặp chính
        while True:
            # Poll dữ liệu
            msg_pack = consumer.poll(timeout_ms=1000)
            
            new_rows = []
            for tp, messages in msg_pack.items():
                for message in messages:
                    record = message.value
                    new_rows.append({
                        'timestamp': record.get('datetime'),
                        'windspeed': float(record.get('windspeed', 0)),
                        'pressure': float(record.get('sealevelpressure', 0))
                    })

            if new_rows:
                # Cập nhật DataFrame
                new_df = pd.DataFrame(new_rows)
                st.session_state.data = pd.concat([st.session_state.data, new_df], ignore_index=True).tail(100)
                
                # Lấy giá trị mới nhất để hiển thị Metric
                latest = new_rows[-1]
                wind = latest['windspeed']
                pressure = latest['pressure']
                
                metric_wind.metric("Gió", f"{wind} km/h", delta_color="inverse")
                metric_pressure.metric("Áp suất", f"{pressure} mb")
                
                if wind > 60:
                    metric_status.error("⚠️ NGUY HIỂM")
                else:
                    metric_status.success("✅ AN TOÀN")

                # Vẽ lại biểu đồ (Dùng placeholder để replace chart cũ)
                with chart_wind_placeholder.container():
                    st.line_chart(st.session_state.data.set_index('timestamp')['windspeed'], height=300)
                
                with chart_pressure_placeholder.container():
                    st.line_chart(st.session_state.data.set_index('timestamp')['pressure'], height=300)
            
            # Sleep nhẹ để giảm tải CPU nếu không có tin nhắn
            time.sleep(0.1)