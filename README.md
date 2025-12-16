
<div align="center">

  <h1>🌪️ Yagi</h1>
  <h3>Yielding Adaptive Geo-spatial Intelligence</h3>
  
  <p>
    <b>From the Storm that broke us, comes the Intelligence that saves us.</b>
  </p>

  <p>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    </a>
    <a href="https://kafka.apache.org/">
      <img src="https://img.shields.io/badge/Apache_Kafka-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white" alt="Kafka">
    </a>
    <a href="https://spark.apache.org/">
      <img src="https://img.shields.io/badge/Apache_Spark-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white" alt="Spark">
    </a>
    <a href="https://www.docker.com/">
      <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
    </a>
    <a href="license">
      <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge" alt="License">
    </a>
  </p>
</div>

<br />

## 📋 Table of Contents

- [About The Project](#-about-the-project)
- [Architecture](#-architecture)
- [Features](#-features)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#-usage)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 📖 About The Project

**Yagi** is an advanced **End-to-End Data Lakehouse & MLOps** system designed for real-time natural disaster warning. This project serves as a comprehensive case study based on the historic **Super Typhoon Yagi (2024)**.

By leveraging **Lambda Architecture** and **Containerization**, Yagi demonstrates how modern Big Data systems ingest, process, store, and analyze massive streams of sensor data to provide life-saving early warnings.

### ❓ Why Yagi?
During Typhoon Yagi, traditional warning systems faced latency and scalability issues. Yagi solves this by:
*   **Streaming First:** Processing data as it arrives (Speed Layer).
*   **ACID Transactions:** Ensuring data integrity with Delta Lake.
*   **ML Integration:** Predicting wind speed and storm trajectory using AI.
*   **Resilience:** Designed to survive infrastructure failures (Chaos Engineering ready).

---

## 🏗 Architecture

The system follows a modernized **Lambda Architecture**, optimized for resource-constrained environments (e.g., 16GB RAM):

![alt text](image.png)

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Ingestion** | **Apache Kafka (KRaft)** | High-throughput message buffer. Zookeeper-less for efficiency. |
| **Speed Layer** | **Spark Streaming** | Real-time processing and immediate hazard detection. |
| **Batch/Serving** | **MinIO + Delta Lake** | Durable storage with Time Travel capabilities. |
| **Intelligence** | **MLOps (Docker/Colab)** | Training models on historical data and deploying inference services. |
| **Visualization** | **Streamlit** | Real-time dashboard for monitoring wind speed and pressure. |

---

## ✨ Features

- **Data Replay Engine**: Simulates IoT sensors transmitting typhoon data from historical CSV logs with adjustable speed.
- **Delta Lake Integration**: Transactional storage layer for reliable Data Lake operations.
- **Real-time Inference**: Dockerized Python service consuming live Kafka streams to predict storm intensity.
- **Auto-Healing**: Capable of recovering from service failures (tested via Chaos Engineering).
- **Multi-channel Alerts**: Instant notifications via Telegram API when critical thresholds are breached.

---

## 🚀 Getting Started

Follow these steps to get a local copy up and running.

### Prerequisites

*   **Docker Desktop** (Engine 20.10+)
*   **Python 3.9+**
*   **Git**

### Installation

1.  **Clone the repo**
    ```sh
    git clone https://github.com/EurusDevSec/Yagi.git
    cd Yagi
    ```

2.  **Environment Setup**
    Create a `.env` file (if required) or configure `docker-compose.yaml` as needed. The default configuration is optimized for local development.

3.  **Start Services**
    Launch the infrastructure using Docker Compose:
    ```sh
    docker-compose up -d
    ```
    *Wait for a few minutes for Kafka and MinIO to initialize fully.*

4.  **Verify Status**
    Check if all containers are healthy:
    ```sh
    docker ps
    ```

---

## 🎮 Usage

### 1. Ingest Data (Simulate Typhoon)
Run the producer script to start replaying the Yagi typhoon data into Kafka:
```sh
python jobs/yagi_producer.py
```

### 2. Start Processing (Spark)
Submit the Spark Streaming job to process the stream and write to Delta Lake:
```sh
docker exec -it spark-master spark-submit --packages io.delta:delta-core_2.12:2.4.0 /jobs/spark_ingestion.py
```

### 3. Launch Dashboard
Access the Streamlit dashboard to view real-time metrics:
```sh
streamlit run dashboard/app.py
```
*Open your browser at `http://localhost:8501`*



---

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📜 License

Distributed under the Apache 2.0 License. See `LICENSE` for more information.

---

## 📞 Contact

**EurusDevSec Team**

Project Link: [https://github.com/EurusDevSec/Yagi](https://github.com/EurusDevSec/Yagi)
