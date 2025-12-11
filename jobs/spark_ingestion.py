from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType


MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password123"
MINIO_ENDPOINT = "http://yagi_minio:9000"
KAFKA_BOOTSTRAP_SERVERS = "yagi_kafka:9092" # Port Internal
TOPIC = "weather-stream"


def main():
    # 1. Khởi tạo Spark Session
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